#!/usr/bin/env python3
"""
Android Course File Upload/Download REST API
Reads configuration from config.toml
"""

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from pathlib import Path
import logging
import time
import tomllib  # Python 3.11+ or use 'tomli' for older versions

app = Flask(__name__)

# Load configuration from config.toml
def load_config():
    """Load configuration from config.toml file"""
    config_file = os.path.join(os.path.dirname(__file__), 'config.toml')
    
    if not os.path.exists(config_file):
        raise FileNotFoundError(
            "config.toml not found. Please run setup_wizard.py first or "
            "copy config.toml.example to config.toml and customize it."
        )
    
    with open(config_file, 'rb') as f:
        return tomllib.load(f)

# Load configuration
try:
    CONFIG = load_config()
except tomllib.TOMLDecodeError as e:
    print(f"Error parsing config.toml: {e}")
    exit(1)
except FileNotFoundError as e:
    print(f"ERROR: {e}")
    exit(1)

# Extract configuration values
BASE_UPLOAD_DIR = CONFIG['paths']['upload_dir']
TOKEN_FILE = os.path.join(CONFIG['paths']['token_dir'], 'tokens.json')
MAX_FILE_SIZE = CONFIG['storage']['max_file_size_mb'] * 1024 * 1024
STUDENT_QUOTA = CONFIG['storage']['student_quota_mb'] * 1024 * 1024
RATE_LIMIT = CONFIG['storage']['rate_limit']
ALLOWED_EXTENSIONS = set(CONFIG['storage']['allowed_extensions'].split(','))

# Rate limiting storage (in production, use Redis)
upload_counts = {}

# Logging setup
log_file = os.path.join(CONFIG['paths']['log_dir'], 'api.log')
os.makedirs(CONFIG['paths']['log_dir'], exist_ok=True)

logging.basicConfig(
    level=getattr(logging, CONFIG['logging']['level']),
    format=CONFIG['logging']['format'],
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"Configuration loaded from config.toml")
logger.info(f"Upload directory: {BASE_UPLOAD_DIR}")
logger.info(f"Token file: {TOKEN_FILE}")


def load_tokens():
    """Load authentication tokens from file"""
    if not os.path.exists(TOKEN_FILE):
        logger.warning(f"Token file not found: {TOKEN_FILE}")
        return {}
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in token file: {TOKEN_FILE}")
        return {}


def validate_token(token):
    """
    Validate authentication token and return associated NetID
    Returns NetID if valid, None if invalid
    """
    if not token:
        return None
    
    tokens = load_tokens()
    
    # Search for token in values, return the key (netid)
    for netid, stored_token in tokens.items():
        if stored_token == token:
            logger.debug(f"Token validated for NetID: {netid}")
            return netid
    
    logger.warning(f"Invalid token attempted")
    return None

def get_student_dir(netid):
    """Get student's upload directory path"""
    student_dir = os.path.join(BASE_UPLOAD_DIR, netid)
    os.makedirs(student_dir, exist_ok=True)
    return student_dir


def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_directory_size(entry.path)
    except PermissionError:
        logger.warning(f"Permission denied calculating size: {path}")
    return total


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_rate_limit(netid):
    """Check if user has exceeded rate limit"""
    if not CONFIG['security']['enable_rate_limiting']:
        return True
    
    now = time.time()
    
    if netid not in upload_counts:
        upload_counts[netid] = []
    
    # Remove old entries (older than 1 minute)
    upload_counts[netid] = [t for t in upload_counts[netid] if now - t < 60]
    
    # Check limit
    if len(upload_counts[netid]) >= RATE_LIMIT:
        return False
    
    # Add current timestamp
    upload_counts[netid].append(now)
    return True


@app.route('/android/upload', methods=['POST'])
def upload_file():
    """Handle file upload via HTTP POST"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        netid = validate_token(token)
        
        if not netid:
            logger.warning(f"Upload attempt with invalid token from {request.remote_addr}")
            return jsonify({'error': 'Invalid or missing authentication token'}), 401
        
        # Check rate limit
        if not check_rate_limit(netid):
            logger.warning(f"Rate limit exceeded for {netid}")
            return jsonify({'error': f'Rate limit exceeded. Maximum {RATE_LIMIT} uploads per minute'}), 429
        
        # Check if file present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed',
                'allowed_types': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f} MB',
                'file_size_mb': file_size / (1024*1024),
                'max_size_mb': MAX_FILE_SIZE / (1024*1024)
            }), 413
        
        # Check quota
        student_dir = get_student_dir(netid)
        current_usage = get_directory_size(student_dir)
        
        if current_usage + file_size > STUDENT_QUOTA:
            remaining = STUDENT_QUOTA - current_usage
            return jsonify({
                'error': 'Quota exceeded',
                'current_usage_mb': current_usage / (1024*1024),
                'quota_mb': STUDENT_QUOTA / (1024*1024),
                'remaining_mb': remaining / (1024*1024),
                'file_size_mb': file_size / (1024*1024)
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
        
        logger.info(f"Upload successful - NetID: {netid}, File: {filename}, Size: {file_size} bytes")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'size_bytes': file_size,
            'current_usage_mb': round((current_usage + file_size) / (1024*1024), 2),
            'quota_mb': STUDENT_QUOTA / (1024*1024)
        }), 201
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/download/<filename>', methods=['GET'])
def download_file(filename):
    """Handle file download via HTTP GET"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        netid = validate_token(token)
        
        if not netid:
            return jsonify({'error': 'Invalid or missing authentication token'}), 401
        
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
        
        logger.info(f"Download successful - NetID: {netid}, File: {filename}")
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/list', methods=['GET'])
def list_files():
    """List all files in student's directory"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        netid = validate_token(token)
        
        if not netid:
            return jsonify({'error': 'Invalid or missing authentication token'}), 401
        
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
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        # Get usage stats
        total_usage = get_directory_size(student_dir)
        
        return jsonify({
            'files': files,
            'total_files': len(files),
            'total_usage_mb': round(total_usage / (1024*1024), 2),
            'quota_mb': STUDENT_QUOTA / (1024*1024),
            'remaining_mb': round((STUDENT_QUOTA - total_usage) / (1024*1024), 2)
        }), 200
        
    except Exception as e:
        logger.error(f"List error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from student's directory"""
    try:
        # Validate token
        token = request.headers.get('X-Auth-Token')
        netid = validate_token(token)
        
        if not netid:
            return jsonify({'error': 'Invalid or missing authentication token'}), 401
        
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
        
        logger.info(f"Delete successful - NetID: {netid}, File: {filename}")
        
        # Get updated usage
        total_usage = get_directory_size(student_dir)
        
        return jsonify({
            'message': 'File deleted successfully',
            'filename': filename,
            'current_usage_mb': round(total_usage / (1024*1024), 2),
            'quota_mb': STUDENT_QUOTA / (1024*1024)
        }), 200
        
    except Exception as e:
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/android/health', methods=['GET'])
def health_check():
    """Health check endpoint (no authentication required)"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200


if __name__ == '__main__':
    # Create base directories
    os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
    os.makedirs(CONFIG['paths']['token_dir'], exist_ok=True)
    os.makedirs(CONFIG['paths']['log_dir'], exist_ok=True)
    
    # Run Flask app (development mode)
    logger.info("Starting Flask development server")
    app.run(
        host=CONFIG['server']['host'],
        port=CONFIG['server']['port'],
        debug=False
    )
