# Android Course File Upload API

REST API for Android Programming students to practice HTTP POST/GET operations with file transfers.

**Course:** Android Programming - Spring 2026  
**Instructor:** Professor Shweta Ware  
**Students:** 18 (17 + instructor)  
**System:** still.richmond.edu  
**User:** installer  

---

## Directory Structure on Spiderweb

```
/scratch/android_course/
├── app/                          # Application code (this repo)
│   ├── app.py                    # Flask REST API
│   ├── android-api.conf          # Apache config
│   ├── android-api.service       # systemd service
│   ├── requirements.txt          # Python dependencies
│   ├── .gitignore                # Git ignore (hides student data)
│   ├── docs/
│   │   ├── STUDENT_GUIDE.md      # API documentation for students
│   │   └── TOKEN_PLACEHOLDER_SNIPPET.md  # For Prof. Ware's starter code
│   ├── scripts/
│   │   ├── generate_tokens.py    # Token management
│   │   ├── cleanup.sh            # Cleanup script
│   │   ├── monitor.sh            # Monitoring script
│   │   └── notify_students.sh    # Notification script
│   ├── sample_files/             # Optional test files for students
│   │   ├── sample_test.txt
│   │   ├── test_data.json
│   │   ├── sensor_data.csv
│   │   ├── test_image.png
│   │   └── README.md
│   ├── policies/
│   │   └── ACCEPTABLE_USE_POLICY.md  # For students (Prof. Ware can modify)
│   └── config/
│       └── tokens.json.template  # Empty template (NOT tokens/tokens.json)
│
├── tokens/                       # Student tokens (GITIGNORED)
│   └── tokens.json               # Created by generate_tokens.py
│
├── logs/                         # Application logs (GITIGNORED)
│   ├── api.log
│   ├── access.log
│   └── error.log
│
└── uploads/                      # Student files (GITIGNORED)
    ├── student1/
    ├── student2/
    └── ...
```

---

## GitHub Repository Setup

### 1. Create GitHub Repo

```bash
# On badenpowell (as cazuza)
cd /android-course-api
git init
git add .
git commit -m "Initial commit - Android Course API"
git remote add origin git@github.com:jtonini/android-course-api.git
git push -u origin main
```

### 2. What Gets Committed to GitHub

**Committed (safe to share):**
- `app.py` - Flask application
- `android-api.conf` - Apache config
- `android-api.service` - systemd service
- `requirements.txt` - Python dependencies
- `docs/` - All documentation
- `scripts/` - Management scripts
- `sample_files/` - Test files
- `policies/` - Policy documents
- `.gitignore` - Git ignore rules
- `config/tokens.json.template` - Empty template

**NOT Committed (in .gitignore):**
- `tokens/` - Student tokens (sensitive!)
- `uploads/` - Student files (private!)
- `logs/` - Application logs
- `__pycache__/` - Python cache

### 3. Clone to Spiderweb

```bash
# On spiderweb (as installer)
cd /scratch/android_course
git clone git@github.com:jtonini/android-course-api.git app
cd app

# Create the gitignored directories
mkdir -p /scratch/android_course/tokens
mkdir -p /scratch/android_course/logs
mkdir -p /scratch/android_course/uploads

# Initialize tokens file
cp config/tokens.json.template /scratch/android_course/tokens/tokens.json
```

---

## Deployment on Spiderweb

### Prerequisites
- User: `installer` (you and Prof. Ware need access)
- Directory: `/scratch/android_course/`
- Anaconda environment available at `/usr/local/sw/anaconda3`

### Setup Steps

#### 1. Clone Repository
```bash
# As installer user on spiderweb
cd /scratch/android_course
git clone git@github.com:jtonini/android-course-api.git app
cd app
```

#### 2. Create Required Directories
```bash
mkdir -p /scratch/android_course/tokens
mkdir -p /scratch/android_course/logs
mkdir -p /scratch/android_course/uploads

# Initialize tokens file
echo '{}' > /scratch/android_course/tokens/tokens.json
chmod 644 /scratch/android_course/tokens/tokens.json
```

#### 3. Install Python Dependencies
```bash
# Using Anaconda
/usr/local/sw/anaconda3/bin/pip install -r requirements.txt
```

#### 4. Install System Services (as root)
```bash
# Copy files
sudo cp /scratch/androi_course/android-api.service /etc/systemd/system/
sudo cp /scratch/android_course/android-api.conf /etc/httpd/conf.d/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable android-api
sudo systemctl start android-api
sudo systemctl restart httpd
```

#### 5. Verify Deployment
```bash
# Check service status
sudo systemctl status android-api

# Test health endpoint
curl https://spiderweb.richmond.edu/android/health
# Should return: {"status":"healthy","timestamp":"..."}

# Check logs
tail -f /scratch/android_course/logs/api.log
```

---

## Token Management

### Generate Tokens for Students

```bash
cd /scratch/android_course/app
/usr/local/sw/anaconda3/bin/python scripts/generate_tokens.py add netid1
/usr/local/sw/anaconda3/bin/python scripts/generate_tokens.py add netid2
```

### Bulk Import from Roster
```bash
# Create students.txt with one NetID per line
cat > students.txt << EOF
student1
student2
student3
EOF

/usr/local/sw/anaconda3/bin/python scripts/generate_tokens.py bulk students.txt
```

### Export for Distribution
```bash
/usr/local/sw/anaconda3/bin/python scripts/generate_tokens.py export tokens_spring2026.csv
```

This creates a CSV that Professor Ware can use to email individual tokens to students.

---

## File Permissions for Prof. Ware Access

Professor Ware needs to access the directory. Two options:

### Option 1: Add her to installer group
```bash
sudo usermod -a -G installer sware
# Prof. Ware logs out and back in
```

### Option 2: Create shared group
```bash
sudo groupadd android-course
sudo usermod -a -G android-course installer
sudo usermod -a -G android-course sware
sudo chgrp -R android-course /scratch/android_course
sudo chmod -R g+rw /scratch/android_course
```

---

## API Endpoints

Base URL: `https://spiderweb.richmond.edu/android`

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/health` | GET | No | Health check |
| `/upload` | POST | Yes | Upload file |
| `/download/<filename>` | GET | Yes | Download file |
| `/list` | GET | Yes | List files |
| `/delete/<filename>` | DELETE | Yes | Delete file |

Authentication: `X-Auth-Token` header with student token

---

## System Limits

- **File size:** 50 MB per file
- **Storage:** 500 MB per student
- **Rate limit:** 10 uploads per minute
- **Total allocation:** 9 GB (18 students × 500 MB)
- **Allowed file types:** txt, pdf, png, jpg, jpeg, gif, json, xml, csv, zip, mp3, mp4, doc, docx

---

## What to Provide Professor Ware

Once deployed, give her:

1. **`docs/TOKEN_PLACEHOLDER_SNIPPET.md`** - Code snippet to add to her starter code
2. **`docs/STUDENT_GUIDE.md`** - Complete API documentation for students
3. **`policies/ACCEPTABLE_USE_POLICY.md`** - Policy she can include in syllabus
4. **`sample_files/`** directory - Optional test files students can use
5. **`tokens_spring2026.csv`** - For emailing individual tokens

---

## Updating the Application

### Pull Updates from GitHub
```bash
cd /scratch/android_course/app
git pull origin main

# If requirements changed
/usr/local/sw/anaconda3/bin/pip install -r requirements.txt

# Restart service
sudo systemctl restart android-api
```

### Push Changes to GitHub
```bash
cd /scratch/android_course/app
git add .
git commit -m "Description of changes"
git push origin main
```

**⚠️ Never commit:**
- `tokens/` directory
- `logs/` directory
- `uploads/` directory
- Any file with student data

The `.gitignore` file protects these automatically.

---

## Monitoring

### Check Service Status
```bash
sudo systemctl status android-api
```

### View Logs
```bash
# Application log
tail -f /scratch/android_course/logs/api.log

# Gunicorn access log
tail -f /scratch/android_course/logs/access.log

# Gunicorn error log
tail -f /scratch/android_course/logs/error.log

# Apache logs
sudo tail -f /var/log/httpd/error_log
sudo tail -f /var/log/httpd/access_log
```

### Use Monitoring Scripts (from João)
```bash
cd /scratch/android_course/app/scripts
./monitor.sh
```

---

## Security Features

✅ Token-based authentication (256-bit tokens)  
✅ HTTPS-only access via Apache  
✅ Per-student directory isolation  
✅ Input sanitization and validation  
✅ File type whitelist  
✅ Rate limiting and quotas  
✅ Audit logging  
✅ FERPA compliant  

---

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u android-api -n 50

# Check if gunicorn is installed
/usr/local/sw/anaconda3/bin/gunicorn --version

# Test app directly
cd /scratch/android_course/app
/usr/local/sw/anaconda3/bin/python app.py
```

### Students can't connect
```bash
# Test proxy
curl http://127.0.0.1:5000/android/health
curl https://spiderweb.richmond.edu/android/health

# Check Apache config
sudo apachectl configtest
sudo systemctl status httpd
```

### Token issues
```bash
# List all tokens
cd /scratch/android_course/app
/usr/local/sw/anaconda3/bin/python scripts/generate_tokens.py list

# Regenerate token
/usr/local/sw/anaconda3/bin/python scripts/generate_tokens.py add netid_to_regenerate
```

---

## Support

**Technical Issues:**
- João Tonini: jtonini@richmond.edu
- Academic Research Computing

**Course Questions:**
- Professor Shweta Ware: sware@richmond.edu

---

## Important Notes

1. **This repo is for APPLICATION CODE only** - student data stays on spiderweb, never in git
2. **The .gitignore protects student privacy** - it blocks tokens/, logs/, uploads/
3. **Professor Ware provides her own starter code** - we only give her the token snippet
4. **Sample files are optional** - she can use them or not
5. **Acceptable Use Policy is a template** - she can modify as needed

---

**Version:** 3.1 (Corrected for installer user + GitHub)  
**Last Updated:** February 4, 2026  
**Maintainer:** João Tonini  
**System:** spiderweb.richmond.edu

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

