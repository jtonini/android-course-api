# Android Course File API

REST API for file upload/download for CS Android Programming course at University of Richmond.

## Features

- File upload (HTTP POST) and download (HTTP GET)
- Per-student directories organized by NetID
- Storage quotas with real-time enforcement
- File type validation (.txt, .log)
- Admin dashboard for monitoring
- Automated cleanup and notification scripts

## Directory Structure

```
/scratch/android_course/
├── app/
│   ├── app.py              # Flask application
│   ├── scripts/
│   │   ├── monitor.sh      # Disk usage monitoring
│   │   ├── cleanup.sh      # End-of-semester cleanup
│   │   └── notify_students.sh  # Student notifications
│   └── docs/
│       └── STUDENT_GUIDE.md    # Student documentation
├── uploads/                # Student files (organized by NetID)
│   ├── ab1cd/
│   ├── xy2zz/
│   └── ...
├── logs/
│   └── api.log            # Application logs
└── backups/               # Backup archives
```

## Quick Start

### Development/Testing

```bash
cd /scratch/android_course/app
/usr/local/sw/anaconda3/bin/python3 app.py
```

### Production (with gunicorn)

```bash
/usr/local/sw/anaconda3/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 app:app
```

## API Endpoints

### Student Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check and API info |
| POST | `/upload` | Upload a file |
| GET | `/download/<student_id>/<filename>` | Download a file |
| GET | `/files/<student_id>` | List student's files |
| GET | `/quota/<student_id>` | Check quota usage |
| DELETE | `/delete/<student_id>/<filename>` | Delete a file |

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/stats` | View all students' usage (requires admin_key) |

## Testing with curl

```bash
# Health check
curl http://localhost:5000/

# Upload a file
curl -X POST \
  -F "student_id=testuser" \
  -F "file=@/path/to/test.txt" \
  http://localhost:5000/upload

# Download a file
curl -O http://localhost:5000/download/testuser/test.txt

# List files
curl http://localhost:5000/files/testuser

# Check quota
curl http://localhost:5000/quota/testuser

# Delete a file
curl -X DELETE http://localhost:5000/delete/testuser/test.txt

# Admin stats (requires API key)
curl -H "X-Admin-Key: changeme-android-admin-2026" \
  http://localhost:5000/admin/stats
```

## Configuration

Edit the top of `app.py` to adjust:

```python
UPLOAD_BASE_DIR = '/scratch/android_course/uploads'
MAX_FILE_SIZE_MB = 50           # Maximum single file size
PER_STUDENT_QUOTA_MB = 500      # Per-student storage limit
TOTAL_COURSE_QUOTA_GB = 15      # Total course storage
MAX_FILES_PER_STUDENT = 100     # Maximum files per student
ALLOWED_EXTENSIONS = {'.txt', '.log'}  # Allowed file types
ADMIN_API_KEY = 'changeme-android-admin-2026'  # Change this!
```

## Scripts

### Monitoring Script

Check disk usage and send email alerts:

```bash
# View current usage
./scripts/monitor.sh

# Send email if thresholds exceeded
./scripts/monitor.sh --email

# Quiet mode (only output warnings)
./scripts/monitor.sh --quiet
```

Recommended cron entry (daily at 8am):
```cron
0 8 * * * /scratch/android_course/app/scripts/monitor.sh --email
```

### Cleanup Script

Remove student data at end of semester:

```bash
# Preview what will be deleted
./scripts/cleanup.sh --dry-run

# Backup and delete
./scripts/cleanup.sh --backup

# Force delete (for cron)
./scripts/cleanup.sh --backup --force
```

### Student Notification Script

Send email reminders about upcoming data deletion:

```bash
# Preview emails
./scripts/notify_students.sh --dry-run

# Send 30-day warning
./scripts/notify_students.sh --days 30

# Send 7-day warning
./scripts/notify_students.sh --days 7
```

## Production Deployment

### 1. Systemd Service

Copy `android-api.service` to `/etc/systemd/system/`:

```bash
sudo cp android-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable android-api
sudo systemctl start android-api
```

### 2. Apache Reverse Proxy

Copy `android-api.conf` to `/etc/httpd/conf.d/`:

```bash
sudo cp android-api.conf /etc/httpd/conf.d/
sudo systemctl reload httpd
```

### 3. Verify

```bash
curl https://spiderweb.richmond.edu/android/
```

## Cron Jobs (Recommended)

Add to crontab for automated maintenance:

```cron
# Daily monitoring at 8am
0 8 * * * /scratch/android_course/app/scripts/monitor.sh --email --quiet

# 30-day deletion warning (May 15)
0 9 15 5 * /scratch/android_course/app/scripts/notify_students.sh --days 30

# 7-day deletion warning (June 8)
0 9 8 6 * /scratch/android_course/app/scripts/notify_students.sh --days 7

# Final cleanup (June 15)
0 0 15 6 * /scratch/android_course/app/scripts/cleanup.sh --backup --force
```

## Maintenance

### View logs
```bash
tail -f /scratch/android_course/logs/api.log
```

### Check disk usage
```bash
du -sh /scratch/android_course/uploads/
du -sh /scratch/android_course/uploads/*/
```

### Restart service
```bash
sudo systemctl restart android-api
```

## Security Notes

- Change `ADMIN_API_KEY` before production deployment
- Debug mode is disabled by default
- All filenames are sanitized to prevent directory traversal
- File extensions are validated
- Quotas prevent storage abuse

## Support

- **Technical Issues:** João Tonini (jtonini@richmond.edu)
- **Course Questions:** Prof. Shweta Ware (sware@richmond.edu)

## License

Internal use only - University of Richmond
