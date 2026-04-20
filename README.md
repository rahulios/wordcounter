# WordCounter (Word Counter Pro)

A Windows desktop app that tracks your writing productivity in real time by
listening to keystrokes, counting words per app/window, and logging daily
progress to an Excel workbook with charts, goals, and analytics.

Built with Tkinter + `pynput`. Optional modules add cloud sync, a login UI,
a mobile companion, payment/subscription handling, and a Flask backend.

## Current main file

[`wordcounter.py`](wordcounter.py) — the active entry point. Older dated
copies live under [`archive/old_versions/`](archive/old_versions/) for
reference only.

## Requirements

- Windows 10/11 (uses `win32gui` / `win32process`)
- Python 3.10+
- Dependencies in `requirements.txt`

## Setup

```powershell
# from the repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python .\wordcounter.py
```

The app tracks keystrokes globally, so on first run Windows may prompt for
accessibility/input permissions.

### Data directory (Windows)

By default, config, Excel data, logs, and backups are stored under:

`%APPDATA%\WordCounterPro\`

(`config.json`, `WordCountData.xlsx`, `word_counter.log`, `backups\`, etc.)

On first run, if those files exist in the **current working directory** (e.g.
repo root) but not yet under `%APPDATA%\WordCounterPro\`, they are copied once
so existing installs migrate cleanly.

Override for development or tests:

```powershell
$env:WORDCOUNTER_DATA_DIR = "C:\path\to\folder"
python .\wordcounter.py
```

`word_count.json` in the repo root is legacy / optional; the app primarily
uses the paths above.

## Project layout

| File / folder | Purpose |
| --- | --- |
| `wordcounter.py` | Current main app |
| `archive/old_versions/` | Archived older `wordcounter *.py` snapshots |
| `%APPDATA%\WordCounterPro\` | Default location for `WordCountData.xlsx`, `config.json`, logs, `backups\` |
| `word_count.json` (repo root) | Legacy optional file; not used by default data dir |
| `ui_improvements.py` | Theme manager and UI polish |
| `mobile_companion.py` | Tkinter "mobile" companion view |
| `payment_system.py` | Stripe / subscription plumbing |
| `auth_ui.py` | Login / register / account dialogs |
| `cloud_sync.py` | Encrypted cloud-sync client |
| `cloud_integration.py` | Glue between app and cloud sync |
| `archive/old_versions/wordcounter_with_cloud.py` | Archived cloud-sync variant (outdated import paths) |
| `backend_server.py` | Local Flask API (dev) |
| `backend_server_production.py` | Production Flask API (Postgres) |
| `setup_cloud_sync.py` | One-time setup helper for cloud sync |
| `deploy_to_heroku.py` | Heroku deploy helper |
| `landing_page.html` | Marketing landing page |
| `Procfile`, `start_backend.bat/.sh` | Backend run helpers |
| `*.md` (ANALYTICS_FEATURES, SECURITY_FEATURES, CLOUD_SYNC_README, ...) | Feature docs |

## Notes

- The Polymarket market-making bot that previously lived in this folder
  has been split out to `C:\Users\1rahu\OneDrive\Polymarket Bot` and has
  its own git repo.
- The repo currently lives under OneDrive, which can occasionally cause
  file-lock / sync issues with `.git/` and `.venv/`. Consider moving the
  source tree out of OneDrive later if that becomes annoying.
