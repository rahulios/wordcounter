# WordCounter (Word Counter Pro)

A Windows desktop app that tracks your writing productivity in real time by
listening to keystrokes, counting words per app/window, and logging daily
progress to an Excel workbook with charts, goals, and analytics.

Built with Tkinter + `pynput`. Optional modules add cloud sync, a login UI,
a mobile companion, payment/subscription handling, and a Flask backend.

## Current main file

`wordcounter 02.06.26.py` — the active version (2,335 lines). Older dated
copies (`wordcounter 09.06.25.py`, `wordcounter 08.03.25.py`, etc.) are kept
around as historical snapshots; they're not part of the runtime.

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
python ".\wordcounter 02.06.26.py"
```

The app tracks keystrokes globally, so on first run Windows may prompt for
accessibility/input permissions. Data is written to `WordCountData.xlsx`
and `word_count.json`; runtime logs go to `word_counter.log`.

## Project layout

| File / folder | Purpose |
| --- | --- |
| `wordcounter 02.06.26.py` | Current main app |
| `wordcounter <date>.py` | Previous dated snapshots (reference only) |
| `WordCountData.xlsx` | Persistent word-count dataset |
| `word_count.json` | Lightweight state / last-session cache |
| `word_counter.log` | Runtime log |
| `config.json` | User-configurable settings |
| `backups/` | Automatic data backups |
| `ui_improvements.py` | Theme manager and UI polish |
| `mobile_companion.py` | Tkinter "mobile" companion view |
| `payment_system.py` | Stripe / subscription plumbing |
| `auth_ui.py` | Login / register / account dialogs |
| `cloud_sync.py` | Encrypted cloud-sync client |
| `cloud_integration.py` | Glue between app and cloud sync |
| `wordcounter_with_cloud.py` | Variant of the app wired to cloud sync |
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
