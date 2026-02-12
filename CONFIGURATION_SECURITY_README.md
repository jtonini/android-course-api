# Configuration Management - Addressing Security Concerns

## Overview

To address IS concerns about sensitive information in GitHub, the Android Course API now uses a **configuration file approach** where site-specific details are NOT committed to version control.

## What's in GitHub (Public)

✅ **Safe to commit:**
- Application code (app.py)
- Configuration template (config.toml.example)
- Setup wizard (setup_wizard.py)
- Documentation
- Scripts
- .gitignore (protects sensitive files)

❌ **Never committed (protected by .gitignore):**
- config.toml (actual configuration)
- tokens/ (student tokens)
- uploads/ (student files)
- logs/ (application logs)

## How It Works

### 1. Developer/Deployer Downloads from GitHub
```bash
git clone https://github.com/jtonini/android-course-api.git
cd android-course-api
```

### 2. Run Setup Wizard
```bash
python3 setup_wizard.py
```

The wizard prompts for:
- Server URLs and hostnames
- Directory paths
- Port numbers
- User accounts
- Security settings
- Storage limits

### 3. Wizard Generates Local Files
```
config.toml              # Site-specific configuration (NOT in git)
android-api.service      # Systemd service with site paths
android-api.conf         # Apache config with site details
```

### 4. Deploy Using Generated Files
The application reads from `config.toml` at runtime, which contains the site-specific configuration.

## What This Protects

### Infrastructure Details (Not in GitHub)
- Internal server paths: `/scratch/android_course/`
- Internal hostnames: `spiderweb.richmond.edu`, `still.richmond.edu`
- Port numbers: `5000`
- Service usernames: `installer`
- Directory structures
- Network configuration

### Why This Matters (Operational Security)
Even though these aren't "secrets," they reveal:
- Internal infrastructure layout
- Software installation locations
- Service architecture
- Potential attack surface

## Deployment Pattern

This is a **standard open-source pattern** used by major projects:

**Example: Database applications**
```
✅ In git: config.example.yml
❌ Not in git: config.yml (actual database credentials)
```

**Example: Web servers**
```
✅ In git: .env.example
❌ Not in git: .env (actual API keys, paths)
```

## Benefits

1. **Security**: No site-specific details in public repository
2. **Portability**: Same code works on any server (spiderweb, still, new VM)
3. **Flexibility**: Easy to change paths/ports without code changes
4. **Documentation**: config.toml.example serves as template
5. **Best Practice**: Industry-standard configuration pattern

## For IS Review

The repository can be made public without exposing:
- University infrastructure details
- Internal network topology
- Service configurations
- Directory layouts

Each deployment generates its own site-specific configuration locally.

## Example: Before vs After

### Before (Hardcoded in app.py - in GitHub)
```python
BASE_UPLOAD_DIR = '/scratch/android_course/uploads'
TOKEN_FILE = '/scratch/android_course/tokens/tokens.json'
LDAP_SERVER = 'ldap://ldap.richmond.edu'
```

### After (Read from config.toml - NOT in GitHub)
```python
CONFIG = load_config()  # Reads config.toml
BASE_UPLOAD_DIR = CONFIG['paths']['upload_dir']
TOKEN_FILE = os.path.join(CONFIG['paths']['token_dir'], 'tokens.json')
```

**Result:** No site-specific paths in GitHub! ✓

## Deployment Steps

1. Clone repository from GitHub
2. Run `python3 setup_wizard.py`
3. Review generated `config.toml`
4. Deploy using generated service files
5. config.toml stays on the server (never committed to git)

## Questions for IS

1. Does this approach address your security concerns?
2. Are there additional fields that should move to config.toml?
3. Should we add encryption for config.toml?
4. Any other recommendations for the configuration approach?

---

**Note:** This is the same pattern used by professional open-source projects to separate code from deployment-specific configuration.
