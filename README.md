# Android Course File Upload/Download API

REST API for Android mobile app development courses. Provides secure file upload/download with per-student authentication and storage quotas.

## Features

- Token-based authentication (one token per student)
- Per-student directory isolation
- Configurable storage quotas (default 500MB per student)
- File size limits (default 50MB per file)
- Rate limiting (10 uploads/minute)
- Multiple file type support
- RESTful API design

## Repository Structure
```
android-course-api/
├── app.py                    # Main Flask application
├── config.toml.example       # Configuration template
├── requirements.txt          # Python dependencies
├── android-api.service       # Systemd service file
├── android-api.conf          # Apache reverse proxy config
├── scripts/                  # Administration tools
│   └── generate_tokens.py    # Token management
├── docs/                     # Documentation
│   ├── API.md               # API documentation
│   └── SECURITY.md          # Security guidelines
└── sample_files/            # Test files
```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/jtonini/android-course-api.git
cd android-course-api
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Deployment
```bash
# Copy example configuration
cp config.toml.example config.toml

# Edit with your server paths
nano config.toml
```

Update these sections:
- `[paths]` - Upload, token, and log directories
- `[storage]` - Quotas and file size limits
- `[service]` - Service user and working directory

### 4. Create Data Directories
```bash
# Example - adjust paths based on your config.toml
mkdir -p /path/to/uploads
mkdir -p /path/to/tokens
mkdir -p /path/to/logs
```

### 5. Generate Student Tokens
```bash
# Add individual student
python scripts/generate_tokens.py add netid1

# Or bulk import from roster
python scripts/generate_tokens.py bulk students.txt

# List all students
python scripts/generate_tokens.py list
```

### 6. Test Locally
```bash
# Run development server
python app.py

# Test health endpoint
curl http://localhost:5000/android/health
```

## Production Deployment

### Option 1: Systemd Service (Recommended)
```bash
# Update android-api.service with your paths
sudo cp android-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable android-api
sudo systemctl start android-api
```

### Option 2: Apache Reverse Proxy
```bash
# For HTTPS access via Apache
sudo cp android-api.conf /etc/httpd/conf.d/
sudo systemctl restart httpd
```

Access API at: `https://yourserver.edu/android/`

## API Endpoints

### Health Check
```bash
GET /android/health
```

### Upload File
```bash
POST /android/upload
Headers: X-Auth-Token: <student_token>
Body: multipart/form-data with 'file' field
```

### List Files
```bash
GET /android/list
Headers: X-Auth-Token: <student_token>
```

### Download File
```bash
GET /android/download/<filename>
Headers: X-Auth-Token: <student_token>
```

## Deployment Configuration

This application uses `config.toml` for deployment-specific settings.

### Quick Start

1. Copy the example configuration:
```bash
   cp config.toml.example config.toml
```

2. Edit `config.toml` with your server paths:
   - Upload directory location
   - Token storage location
   - Log directory
   - Service user/group

3. **Important:** Never commit `config.toml` - it's protected by `.gitignore`

### Production Deployment

- Uses systemd service: `android-api.service`
- Apache reverse proxy: `android-api.conf`
- Runs as dedicated service user

See `config.toml.example` for all configuration options.

## Security

- **Never commit `config.toml`** - contains deployment paths
- **Never commit `tokens/`** - contains authentication tokens
- **Never commit `uploads/`** - contains student data
- **Never commit `logs/`** - may contain sensitive info

All sensitive directories are protected by `.gitignore`.

## Token Management
```bash
# Add single student
python scripts/generate_tokens.py add studentID

# Remove student
python scripts/generate_tokens.py remove studentID

# Import from file (one NetID per line)
python scripts/generate_tokens.py bulk roster.txt

# Export to CSV for distribution
python scripts/generate_tokens.py export tokens.csv

# List all registered students
python scripts/generate_tokens.py list
```

## Monitoring
```bash
# View service logs
sudo journalctl -u android-api -f

# View application logs (path from config.toml)
tail -f /path/to/logs/api.log

# View Apache logs (if using reverse proxy)
tail -f /var/log/httpd/access_log
tail -f /var/log/httpd/error_log
```

## Troubleshooting

### Service won't start
```bash
# Check service status
sudo systemctl status android-api

# Check logs
sudo journalctl -u android-api -n 50

# Verify config.toml exists and is valid
python -c "import tomllib; tomllib.load(open('config.toml', 'rb'))"
```

### Upload fails
- Check directory permissions
- Verify token is valid
- Check storage quota not exceeded
- Verify file size under limit

### API not accessible
- Check service is running
- Verify Apache proxy configuration
- Check firewall rules
- Test direct access: `curl http://localhost:5000/android/health`

## Development

### Running Tests
```bash
# Manual testing
python app.py

# Test upload
TOKEN="your_test_token"
curl -X POST -H "X-Auth-Token: $TOKEN" \
  -F "file=@test.txt" \
  http://localhost:5000/android/upload
```

### Code Structure
- `app.py` - Main Flask application
- `scripts/generate_tokens.py` - Token management
- `config.toml.example` - Configuration template
- `android-api.service` - Systemd service definition
- `android-api.conf` - Apache reverse proxy config

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

For educational use in mobile app development courses.

## Support

For issues or questions, contact your system administrator or course instructor.
