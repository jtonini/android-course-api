#!/usr/bin/env python3
"""
Android Course File Upload/Download REST API
Supports HTTP POST for file uploads and HTTP GET for downloads
Per-student directory isolation with quotas and rate limiting
"""

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

app = Flask(__name__)

# Configuration
BASE_UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/scratch/android_course/uploads')
TOKEN_FILE = os.environ.get('TOKEN_FILE', '/scratch/android_course/tokens/tokens.json')
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
STUDENT_QUOTA = 500 * 1024 * 1024  # 500 MB per student
RATE_LIMIT = 10  # uploads per minute
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'json', 'xml', 
    'csv', 'zip', 'mp3', 'mp4', 'doc', 'docx'
}

# Rate limiting storage (in production, use Redis)
upload_counts = {}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/scratch/android_course/logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_tokens():
    """Load student tokens from JSON file"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Token file not found: {TOKEN_FILE}")
        return {}


def validate_token(token):
    """Validate token and return student netid"""
    tokens = load_tokens()
    for netid, student_token in tokens.items():
        if student_token == token:
            return netid
    return None


def get_student_dir(netid):
    """Get student's upload directory path"""
    student_dir = os.path.join(BASE_UPLOAD_DIR, netid)
    os.makedirs(student_dir, exist_ok=True)
    return student_dir


def get_directory_size(path):
    """Calculate total size of directory"""
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += get_directory_size(entry.path)
    return total


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_rate_limit(netid):
    """Check if student has exceeded upload rate limit"""
    current_time = time.time()
    
    if netid not in upload_counts:
        upload_counts[netid] = []
    
    # Remove uploads older than 1 minute
    upload_counts[netid] = [t for t in upload_counts[netid] if current_time - t < 60]
    
    if len(upload_counts[netid]) >= RATE_LIMIT:
        return False
    
    upload_counts[netid].append(current_time)
    return True


@app.route('/android/upload', methods=['POST'])
def upload_file():
    """Handle file upload via HTTP POST"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        if not token:
            logger.warning("Upload attempt without token")
            return jsonify({'error': 'Missing authentication token'}), 401
        
        netid = validate_token(token)
        if not netid:
            logger.warning(f"Invalid token attempt: {token[:8]}...")
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Check rate limit
        if not check_rate_limit(netid):
            logger.warning(f"Rate limit exceeded for {netid}")
            return jsonify({'error': 'Rate limit exceeded. Maximum 10 uploads per minute'}), 429
        
        # Check if file present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f} MB'}), 413
        
        # Check quota
        student_dir = get_student_dir(netid)
        current_usage = get_directory_size(student_dir)
        
        if current_usage + file_size > STUDENT_QUOTA:
            remaining = STUDENT_QUOTA - current_usage
            return jsonify({
                'error': 'Quota exceeded',
                'current_usage_mb': current_usage / (1024*1024),
                'quota_mb': STUDENT_QUOTA / (1024*1024),
                'remaining_mb': remaining / (1024*1024)
            }), 507
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(student_dir, filename)
        
        # Handle duplicate filenames
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(filepath):
            filename = f"{base}_{counter}{ext}"
            filepath = os.path.join(student_dir, filename)
            counter += 1
        
        file.save(filepath)
        
        # Log successful upload
        logger.info(f"Upload successful - NetID: {netid}, File: {filename}, Size: {file_size} bytes")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'size_bytes': file_size,
            'current_usage_mb': (current_usage + file_size) / (1024*1024),
            'quota_mb': STUDENT_QUOTA / (1024*1024)
        }), 201
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/download/<filename>', methods=['GET'])
def download_file(filename):
    """Handle file download via HTTP GET"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        if not token:
            logger.warning("Download attempt without token")
            return jsonify({'error': 'Missing authentication token'}), 401
        
        netid = validate_token(token)
        if not netid:
            logger.warning(f"Invalid token attempt: {token[:8]}...")
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Get student directory
        student_dir = get_student_dir(netid)
        filepath = os.path.join(student_dir, secure_filename(filename))
        
        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(student_dir)):
            logger.warning(f"Directory traversal attempt by {netid}: {filename}")
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Log successful download
        logger.info(f"Download successful - NetID: {netid}, File: {filename}")
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/list', methods=['GET'])
def list_files():
    """List all files in student's directory"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401
        
        netid = validate_token(token)
        if not netid:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Get student directory
        student_dir = get_student_dir(netid)
        
        # List files
        files = []
        for entry in os.scandir(student_dir):
            if entry.is_file():
                stat = entry.stat()
                files.append({
                    'filename': entry.name,
                    'size_bytes': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Get usage stats
        total_usage = get_directory_size(student_dir)
        
        return jsonify({
            'files': files,
            'total_files': len(files),
            'total_usage_mb': total_usage / (1024*1024),
            'quota_mb': STUDENT_QUOTA / (1024*1024),
            'remaining_mb': (STUDENT_QUOTA - total_usage) / (1024*1024)
        }), 200
        
    except Exception as e:
        logger.error(f"List error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from student's directory"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401
        
        netid = validate_token(token)
        if not netid:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Get student directory
        student_dir = get_student_dir(netid)
        filepath = os.path.join(student_dir, secure_filename(filename))
        
        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(student_dir)):
            logger.warning(f"Directory traversal attempt by {netid}: {filename}")
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Delete file
        os.remove(filepath)
        
        # Log successful deletion
        logger.info(f"Delete successful - NetID: {netid}, File: {filename}")
        
        # Get updated usage
        total_usage = get_directory_size(student_dir)
        
        return jsonify({
            'message': 'File deleted successfully',
            'filename': filename,
            'current_usage_mb': total_usage / (1024*1024),
            'quota_mb': STUDENT_QUOTA / (1024*1024)
        }), 200
        
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    # Create base upload directory
    os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
