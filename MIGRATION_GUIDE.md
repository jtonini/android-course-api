# Migration Guide - Adding Configuration File Support

## Quick Update Steps

### 1. Add New Files to Repository

```bash
cd /path/to/android-course-api

# Add configuration template
cp /path/to/config.toml.example .

# Add setup wizard
cp /path/to/setup_wizard.py .

# Update .gitignore
cat >> .gitignore << 'EOF'

# Configuration - NEVER COMMIT
config.toml
*.toml
!config.toml.example
EOF

# Update requirements.txt
echo 'tomli==2.0.1; python_version < '"'"'3.11'"'"'' >> requirements.txt

# Add to git
git add config.toml.example setup_wizard.py .gitignore requirements.txt
git commit -m "Add configuration file support for security"
git push
```

### 2. Replace app.py

Replace the current app.py with the config-aware version:

```bash
# Backup current version
cp app.py app.py.backup

# Copy new version
cp /path/to/app_with_config.py app.py

# Commit
git add app.py
git commit -m "Update app.py to read from config.toml"
git push
```

### 3. Generate Configuration on Server

On spiderweb (or wherever deployed):

```bash
cd /scratch/android_course/app

# Pull latest changes
git pull

# Install updated dependencies
/usr/local/sw/anaconda3/bin/pip install -r requirements.txt

# Run setup wizard (or create config.toml manually)
/usr/local/sw/anaconda3/bin/python setup_wizard.py
```

**Wizard will prompt for:**
- Public URL: `https://spiderweb.richmond.edu/android`
- Flask host: `127.0.0.1`
- Flask port: `5000`
- Upload dir: `/scratch/android_course/uploads`
- Token dir: `/scratch/android_course/tokens`
- Log dir: `/scratch/android_course/logs`
- Service user: `installer`
- etc.

### 4. Verify Configuration

```bash
# Check config.toml was created
cat config.toml

# Verify it's gitignored
git status  # config.toml should NOT appear

# Test the app
/usr/local/sw/anaconda3/bin/python app.py
# In another terminal: curl http://localhost:5000/android/health
```

### 5. Restart Service

```bash
# If service is running
sudo systemctl restart android-api

# Verify
curl https://spiderweb.richmond.edu/android/health
```

## Manual config.toml Creation

If you prefer to skip the wizard and create config.toml manually:

```bash
cd /scratch/android_course/app
cp config.toml.example config.toml
nano config.toml
```

Edit the values to match your deployment:

```toml
[server]
base_url = "https://spiderweb.richmond.edu/android"
host = "127.0.0.1"
port = 5000
workers = 2
timeout = 120

[paths]
upload_dir = "/scratch/android_course/uploads"
token_dir = "/scratch/android_course/tokens"
log_dir = "/scratch/android_course/logs"

[storage]
max_file_size_mb = 50
student_quota_mb = 500
rate_limit = 10
allowed_extensions = "txt,pdf,png,jpg,jpeg,gif,json,xml,csv,zip,mp3,mp4,doc,docx"

[logging]
level = "INFO"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

[security]
require_https = true
enable_rate_limiting = true

[service]
user = "installer"
group = "installer"
working_dir = "/scratch/android_course/app"
python_path = "/usr/local/sw/anaconda3/bin/python"
gunicorn_path = "/usr/local/sw/anaconda3/bin/gunicorn"

[apache]
conf_dir = "/etc/httpd/conf.d"
location = "/android"
max_request_body_mb = 52
```

## Rollback Plan

If something goes wrong:

```bash
# Restore old app.py
cp app.py.backup app.py

# Remove config requirement
git revert HEAD

# Restart service
sudo systemctl restart android-api
```

## Verification Checklist

After migration:

- [ ] config.toml exists and has correct values
- [ ] config.toml does NOT appear in `git status`
- [ ] App starts without errors: `python app.py`
- [ ] Health endpoint works: `curl http://localhost:5000/android/health`
- [ ] Service restarts successfully: `sudo systemctl restart android-api`
- [ ] Public endpoint works: `curl https://spiderweb.richmond.edu/android/health`
- [ ] Uploads still work (test with token)
- [ ] Logs are written to correct location

## Benefits of This Migration

1. **Security**: No site-specific paths in GitHub
2. **Flexibility**: Easy to change configuration without code changes
3. **Portability**: Same code works on spiderweb, still, or new VM
4. **IS Approval**: Addresses their security concerns

## Questions?

Contact João (jtonini@richmond.edu) if you have issues during migration.
