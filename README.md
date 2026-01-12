# Android Course File API

REST API for file upload/download for CS Android Programming course.

## Directory Structure

```
/scratch/android_course/
├── app/
│   └── app.py          # Flask application
├── uploads/            # Student files (organized by NetID)
│   ├── ab1cd/
│   ├── xy2zz/
│   └── ...
└── logs/
    └── api.log         # Application logs
```

## Quick Start (Testing)

```bash
# Navigate to app directory
cd /scratch/android_course/app

# Run with Flask development server (for testing only)
/usr/local/sw/anaconda3/bin/python3 app.py

# Or run with gunicorn (production)
/usr/local/sw/anaconda3/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check and API info |
| POST | `/upload` | Upload a file |
| GET | `/download/<student_id>/<filename>` | Download a file |
| GET | `/files/<student_id>` | List student's files |
| GET | `/quota/<student_id>` | Check quota usage |
| DELETE | `/delete/<student_id>/<filename>` | Delete a file |

## Testing with curl

### Upload a file
```bash
curl -X POST \
  -F "student_id=testuser" \
  -F "file=@/path/to/test.txt" \
  http://localhost:5000/upload
```

### Download a file
```bash
curl -O http://localhost:5000/download/testuser/test.txt
```

### List files
```bash
curl http://localhost:5000/files/testuser
```

### Check quota
```bash
curl http://localhost:5000/quota/testuser
```

### Delete a file
```bash
curl -X DELETE http://localhost:5000/delete/testuser/test.txt
```

## Configuration

Edit the top of `app.py` to adjust:

- `UPLOAD_BASE_DIR` - Where files are stored
- `MAX_FILE_SIZE_MB` - Maximum single file size (default: 50 MB)
- `PER_STUDENT_QUOTA_MB` - Per-student storage limit (default: 500 MB)
- `TOTAL_COURSE_QUOTA_GB` - Total course storage limit (default: 15 GB)
- `MAX_FILES_PER_STUDENT` - Maximum files per student (default: 100)
- `ALLOWED_EXTENSIONS` - Allowed file types (default: .txt, .log)

## Production Deployment

### 1. Start with systemd (requires root)

Create `/etc/systemd/system/android-api.service`:

```ini
[Unit]
Description=Android Course File API
After=network.target

[Service]
User=installer
Group=installer
WorkingDirectory=/scratch/android_course/app
ExecStart=/usr/local/sw/anaconda3/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable android-api
sudo systemctl start android-api
```

### 2. Configure Apache reverse proxy (requires root)

Add to Apache configuration:

```apache
# Android Course API
ProxyPass /android http://127.0.0.1:5000
ProxyPassReverse /android http://127.0.0.1:5000
```

## Student Documentation

Students access the API at: `https://spiderweb.richmond.edu/android/`

Example Android code:
```java
// Upload
URL url = new URL("https://spiderweb.richmond.edu/android/upload");
HttpURLConnection conn = (HttpURLConnection) url.openConnection();
conn.setRequestMethod("POST");
conn.setDoOutput(true);
// ... add multipart form data with student_id and file

// Download
URL url = new URL("https://spiderweb.richmond.edu/android/download/ab1cd/myfile.txt");
InputStream in = url.openStream();
// ... read file
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

### End of semester cleanup
```bash
# Backup if needed
tar -czf android_course_backup_$(date +%Y%m%d).tar.gz /scratch/android_course/uploads/

# Remove all student data
rm -rf /scratch/android_course/uploads/*
```
