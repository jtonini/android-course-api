#!/usr/bin/env python3
"""
Android Course File Upload/Download REST API
University of Richmond - Spiderweb Server

This Flask application provides HTTP POST/GET endpoints for students
to upload and download files from their Android applications.

Features:
- Per-student directories (organized by NetID)
- Storage quotas (configurable per-student and total)
- File size limits
- File type validation
- Logging

Author: João Tonini, HPC Systems Administrator
Course: CS XXX - Android Programming (Prof. Shweta Ware)
Semester: Spring 2026
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, send_file, jsonify

# =============================================================================
# CONFIGURATION
# =============================================================================

# Base directory for all uploads
UPLOAD_BASE_DIR = '/scratch/android_course/uploads'

# Log file location
LOG_FILE = '/scratch/android_course/logs/api.log'

# Storage limits
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

PER_STUDENT_QUOTA_MB = 500
PER_STUDENT_QUOTA_BYTES = PER_STUDENT_QUOTA_MB * 1024 * 1024

TOTAL_COURSE_QUOTA_GB = 15
TOTAL_COURSE_QUOTA_BYTES = TOTAL_COURSE_QUOTA_GB * 1024 * 1024 * 1024

MAX_FILES_PER_STUDENT = 100

# Allowed file extensions (set to None to allow all, or list specific ones)
ALLOWED_EXTENSIONS = {'.txt', '.log'}  # As requested by faculty

# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_BYTES

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_directory_size(path):
    """Calculate total size of a directory in bytes."""
    total_size = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
    return total_size

def get_file_count(path):
    """Count total number of files in a directory."""
    count = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            count += len(filenames)
    return count

def is_valid_netid(netid):
    """Validate NetID format (alphanumeric, reasonable length)."""
    if not netid:
        return False
    if len(netid) < 2 or len(netid) > 20:
        return False
    return netid.isalnum()

def is_allowed_file(filename):
    """Check if file extension is allowed."""
    if ALLOWED_EXTENSIONS is None:
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def secure_filename(filename):
    """Sanitize filename to prevent directory traversal attacks."""
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove potentially dangerous characters
    keepcharacters = (' ', '.', '_', '-')
    filename = "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed_file'
    return filename

def format_size(bytes_size):
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/')
def index():
    """Health check and API info."""
    return jsonify({
        'service': 'Android Course File API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'POST /upload': 'Upload a file (requires student_id and file)',
            'GET /download/<student_id>/<filename>': 'Download a file',
            'GET /files/<student_id>': 'List files for a student',
            'GET /quota/<student_id>': 'Check quota usage',
            'DELETE /delete/<student_id>/<filename>': 'Delete a file'
        }
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload a file for a student.
    
    Required form fields:
    - student_id: The student's NetID
    - file: The file to upload
    
    Returns:
    - JSON response with success status and file info
    """
    # Validate student_id
    student_id = request.form.get('student_id', '').strip().lower()
    if not is_valid_netid(student_id):
        logger.warning(f"Invalid student_id attempted: {student_id}")
        return jsonify({
            'success': False,
            'error': 'Invalid student_id. Must be alphanumeric, 2-20 characters.'
        }), 400
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided. Include a file with key "file".'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected.'
        }), 400
    
    # Sanitize filename
    filename = secure_filename(file.filename)
    
    # Check file extension
    if not is_allowed_file(filename):
        allowed = ', '.join(ALLOWED_EXTENSIONS) if ALLOWED_EXTENSIONS else 'all'
        return jsonify({
            'success': False,
            'error': f'File type not allowed. Allowed types: {allowed}'
        }), 400
    
    # Create student directory if it doesn't exist
    student_dir = os.path.join(UPLOAD_BASE_DIR, student_id)
    os.makedirs(student_dir, exist_ok=True)
    
    # Check total course quota
    total_usage = get_directory_size(UPLOAD_BASE_DIR)
    if total_usage >= TOTAL_COURSE_QUOTA_BYTES:
        logger.error(f"Course quota exceeded. Total usage: {format_size(total_usage)}")
        return jsonify({
            'success': False,
            'error': 'Course storage limit reached. Contact instructor.'
        }), 507
    
    # Check student quota
    student_usage = get_directory_size(student_dir)
    
    # Read file content to check size
    file_content = file.read()
    file_size = len(file_content)
    
    if student_usage + file_size > PER_STUDENT_QUOTA_BYTES:
        return jsonify({
            'success': False,
            'error': f'Quota exceeded. You have used {format_size(student_usage)} of {format_size(PER_STUDENT_QUOTA_BYTES)}. '
                     f'This file ({format_size(file_size)}) would exceed your limit.'
        }), 413
    
    # Check file count
    file_count = get_file_count(student_dir)
    if file_count >= MAX_FILES_PER_STUDENT:
        return jsonify({
            'success': False,
            'error': f'Maximum file count ({MAX_FILES_PER_STUDENT}) reached. Delete some files first.'
        }), 413
    
    # Save the file
    filepath = os.path.join(student_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(file_content)
    
    logger.info(f"File uploaded: {student_id}/{filename} ({format_size(file_size)})")
    
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully.',
        'filename': filename,
        'size': file_size,
        'size_formatted': format_size(file_size),
        'quota_used': student_usage + file_size,
        'quota_used_formatted': format_size(student_usage + file_size),
        'quota_limit_formatted': format_size(PER_STUDENT_QUOTA_BYTES)
    }), 201


@app.route('/download/<student_id>/<filename>', methods=['GET'])
def download_file(student_id, filename):
    """
    Download a file for a student.
    
    URL parameters:
    - student_id: The student's NetID
    - filename: The name of the file to download
    
    Returns:
    - The file as an attachment
    """
    # Validate student_id
    student_id = student_id.strip().lower()
    if not is_valid_netid(student_id):
        return jsonify({
            'success': False,
            'error': 'Invalid student_id.'
        }), 400
    
    # Sanitize filename
    filename = secure_filename(filename)
    
    # Build filepath
    filepath = os.path.join(UPLOAD_BASE_DIR, student_id, filename)
    
    # Check if file exists
    if not os.path.isfile(filepath):
        return jsonify({
            'success': False,
            'error': 'File not found.'
        }), 404
    
    logger.info(f"File downloaded: {student_id}/{filename}")
    
    return send_file(filepath, as_attachment=True, attachment_filename=filename)


@app.route('/files/<student_id>', methods=['GET'])
def list_files(student_id):
    """
    List all files for a student.
    
    URL parameters:
    - student_id: The student's NetID
    
    Returns:
    - JSON list of files with metadata
    """
    # Validate student_id
    student_id = student_id.strip().lower()
    if not is_valid_netid(student_id):
        return jsonify({
            'success': False,
            'error': 'Invalid student_id.'
        }), 400
    
    student_dir = os.path.join(UPLOAD_BASE_DIR, student_id)
    
    if not os.path.exists(student_dir):
        return jsonify({
            'success': True,
            'student_id': student_id,
            'files': [],
            'total_size': 0,
            'total_size_formatted': '0 B'
        })
    
    files = []
    total_size = 0
    
    for filename in os.listdir(student_dir):
        filepath = os.path.join(student_dir, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            size = stat.st_size
            total_size += size
            files.append({
                'filename': filename,
                'size': size,
                'size_formatted': format_size(size),
                'uploaded': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    # Sort by upload time (newest first)
    files.sort(key=lambda x: x['uploaded'], reverse=True)
    
    return jsonify({
        'success': True,
        'student_id': student_id,
        'files': files,
        'file_count': len(files),
        'total_size': total_size,
        'total_size_formatted': format_size(total_size)
    })


@app.route('/quota/<student_id>', methods=['GET'])
def check_quota(student_id):
    """
    Check quota usage for a student.
    
    URL parameters:
    - student_id: The student's NetID
    
    Returns:
    - JSON with quota information
    """
    # Validate student_id
    student_id = student_id.strip().lower()
    if not is_valid_netid(student_id):
        return jsonify({
            'success': False,
            'error': 'Invalid student_id.'
        }), 400
    
    student_dir = os.path.join(UPLOAD_BASE_DIR, student_id)
    
    used = get_directory_size(student_dir)
    file_count = get_file_count(student_dir)
    available = max(0, PER_STUDENT_QUOTA_BYTES - used)
    percentage = (used / PER_STUDENT_QUOTA_BYTES) * 100 if PER_STUDENT_QUOTA_BYTES > 0 else 0
    
    return jsonify({
        'success': True,
        'student_id': student_id,
        'quota': {
            'used': used,
            'used_formatted': format_size(used),
            'limit': PER_STUDENT_QUOTA_BYTES,
            'limit_formatted': format_size(PER_STUDENT_QUOTA_BYTES),
            'available': available,
            'available_formatted': format_size(available),
            'percentage_used': round(percentage, 1)
        },
        'files': {
            'count': file_count,
            'limit': MAX_FILES_PER_STUDENT
        }
    })


@app.route('/delete/<student_id>/<filename>', methods=['DELETE'])
def delete_file(student_id, filename):
    """
    Delete a file for a student.
    
    URL parameters:
    - student_id: The student's NetID
    - filename: The name of the file to delete
    
    Returns:
    - JSON response with success status
    """
    # Validate student_id
    student_id = student_id.strip().lower()
    if not is_valid_netid(student_id):
        return jsonify({
            'success': False,
            'error': 'Invalid student_id.'
        }), 400
    
    # Sanitize filename
    filename = secure_filename(filename)
    
    # Build filepath
    filepath = os.path.join(UPLOAD_BASE_DIR, student_id, filename)
    
    # Check if file exists
    if not os.path.isfile(filepath):
        return jsonify({
            'success': False,
            'error': 'File not found.'
        }), 404
    
    # Delete the file
    file_size = os.path.getsize(filepath)
    os.remove(filepath)
    
    logger.info(f"File deleted: {student_id}/{filename}")
    
    return jsonify({
        'success': True,
        'message': 'File deleted successfully.',
        'filename': filename,
        'freed_space': file_size,
        'freed_space_formatted': format_size(file_size)
    })


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size is {MAX_FILE_SIZE_MB} MB.'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found.'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again later.'
    }), 500


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
    
    # Run development server (use gunicorn in production)
    print(f"Starting Android Course File API...")
    print(f"Upload directory: {UPLOAD_BASE_DIR}")
    print(f"Per-student quota: {PER_STUDENT_QUOTA_MB} MB")
    print(f"Max file size: {MAX_FILE_SIZE_MB} MB")
    app.run(host='0.0.0.0', port=5000, debug=True)
