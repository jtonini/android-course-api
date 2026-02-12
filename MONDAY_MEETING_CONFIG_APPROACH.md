# For Monday Meeting - Configuration Security Approach

## IS Concern
"Sensitive information on GitHub" (they haven't specified what)

## Likely Concerns
Even though we have .gitignore protecting tokens/uploads/logs, IS is probably concerned about **operational security** information being public:

1. Server paths: `/scratch/android_course/`
2. Internal hostnames: `spiderweb.richmond.edu`, `still.richmond.edu`
3. Port numbers: `5000`
4. Service users: `installer`
5. Directory structures
6. Infrastructure details

## Solution: Configuration File Pattern

### Industry-Standard Approach
```
GitHub (public):
├── app.py (code that reads config)
├── config.toml.example (template)
├── setup_wizard.py (generates config)
└── .gitignore (blocks config.toml)

Server (private):
└── config.toml (actual site-specific settings)
```

### How It Works

**Step 1:** Developer clones from GitHub
```bash
git clone https://github.com/jtonini/android-course-api.git
```

**Step 2:** Run setup wizard
```bash
python3 setup_wizard.py
```

Wizard prompts for:
- Upload directory path
- Token directory path
- Log directory path
- Server hostname
- Port number
- Service user
- etc.

**Step 3:** Wizard generates local files
- `config.toml` (site-specific, NOT in git)
- `android-api.service` (with site paths)
- `android-api.conf` (with site configuration)

**Step 4:** App reads from config.toml
```python
CONFIG = load_config()  # Reads config.toml
BASE_UPLOAD_DIR = CONFIG['paths']['upload_dir']
```

### What's Protected

**Before (currently in GitHub):**
```python
# Hardcoded in app.py
BASE_UPLOAD_DIR = '/scratch/android_course/uploads'
```

**After (NOT in GitHub):**
```toml
# In config.toml (gitignored)
[paths]
upload_dir = "/scratch/android_course/uploads"
```

**In GitHub:**
```python
# In app.py
CONFIG = load_config()
BASE_UPLOAD_DIR = CONFIG['paths']['upload_dir']
```

## Benefits

1. ✅ **No site-specific details in GitHub**
2. ✅ **Same code works on any server** (spiderweb, still, new VM)
3. ✅ **Easy to reconfigure** without code changes
4. ✅ **Industry best practice**
5. ✅ **Repository can be public** safely

## For the Meeting

### Explain to IS:

```
"We understand your security concerns. We're implementing a configuration 
file approach - the industry standard for separating code from deployment 
details.

The GitHub repository will only contain:
- Application code
- Configuration template (example only)
- Setup wizard

Site-specific information (paths, hostnames, ports) will be in a local 
config.toml file that's never committed to git.

This is the same pattern used by major projects like databases, web servers, 
and cloud applications to keep deployment details private.

Does this address your concerns?"
```

### If They Ask for Details:

Show them:
1. `config.toml.example` (what's in GitHub - template only)
2. `.gitignore` (shows config.toml is blocked)
3. `setup_wizard.py` (generates site-specific config)
4. `CONFIGURATION_SECURITY_README.md` (full explanation)

### Files to Bring to Meeting:

1. CONFIGURATION_SECURITY_README.md
2. config.toml.example
3. setup_wizard.py
4. Updated .gitignore

## Implementation Timeline

If IS approves this approach:
- **Today/Tomorrow:** Update code to use config.toml
- **Before Monday:** Test on spiderweb
- **Monday meeting:** Present approach to IS
- **After approval:** Can make repo public if desired

## Questions to Ask IS

1. Does this configuration approach address your concerns?
2. Are there additional items that should be in config.toml?
3. Should we encrypt config.toml on the server?
4. Any other security recommendations?

## This is Not New Work

This is a **standard pattern** - we're just applying it to this project. Similar to how:
- Database apps use `database.yml.example` (in git) and `database.yml` (not in git)
- Web apps use `.env.example` (in git) and `.env` (not in git)
- Config management tools use templates and local overrides

---

**Bottom Line:** This is a reasonable, professional approach that addresses security concerns while following industry best practices.
