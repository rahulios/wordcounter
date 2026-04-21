# WordCounter

A Windows desktop app that tracks your writing productivity by counting
words typed in the **writing apps you care about** (Obsidian, Microsoft
Word, Evernote, Scrivener, Notepad++, etc.) and logging daily progress
to an Excel workbook with charts, goals, and analytics.

Built with Tkinter + `pynput` + `pywin32`.

## Privacy model

This app is **not** a general keystroke logger. By design:

- A foreground-window hook watches which app is focused.
- The keyboard listener is **only instantiated while an allowlisted
  writing app is focused**. When you alt-tab to Chrome, Slack, your
  password manager, or anything else, the listener is stopped and the
  process receives zero keystrokes.
- Only aggregate word counts are persisted. The in-memory `current_word`
  buffer is short-lived and zeroed on app-switch, pause, stop, and blur.
- No cloud uploads, no telemetry, no network calls in v1.

See `AppFocusManager` and `FocusWatcher` in [`wordcounter.py`](wordcounter.py).

## Requirements

- Windows 10/11 (uses `win32gui` / `win32process` / `SetWinEventHook`)
- Python 3.10+
- Dependencies in [`requirements.txt`](requirements.txt)

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

The keyboard hook `pynput` uses may trigger a one-time Windows permission
prompt on first run.

## Default allowlist

First-run wizard lets you confirm / edit, but the baseline shipped is:

- `winword.exe` (Microsoft Word)
- `obsidian.exe`
- `evernote.exe`
- `scrivener.exe`
- `notepad.exe`, `notepad++.exe`
- `sublime_text.exe`
- `typora.exe`, `wordpad.exe`
- (any additional installed writing app the wizard detects)

Browser-based writing (Google Docs, Notion web, Substack) is **not** tracked
in v1. Adding those is planned for the Public Beta milestone.

## Data directory (Windows)

By default, config, Excel data, logs, and backups are stored under:

`%APPDATA%\WordCounterPro\`

(`config.json`, `WordCountData.xlsx`, `word_counter.log`, `backups\`, etc.)

On first run, if those files exist in the current working directory but not
yet under `%APPDATA%\WordCounterPro\`, they are copied once so existing
installs migrate cleanly.

Override for development or tests:

```powershell
$env:WORDCOUNTER_DATA_DIR = "C:\path\to\folder"
python .\wordcounter.py
```

## Project layout

| File / folder | Purpose |
| --- | --- |
| [`wordcounter.py`](wordcounter.py) | Current main app |
| [`ui_improvements.py`](ui_improvements.py) | Theme manager reference (not imported yet; kept for upcoming UI polish) |
| [`requirements.txt`](requirements.txt) | Runtime dependencies |
| `%APPDATA%\WordCounterPro\` | Default location for `WordCountData.xlsx`, `config.json`, logs, `backups\` |
| `word_count.json` (repo root) | Legacy optional file; not used by default data dir |
| [`archive/old_versions/`](archive/old_versions/) | Older dated `wordcounter *.py` snapshots for reference |
| [`archive/product-infra-2025/`](archive/product-infra-2025/) | Parked: cloud sync, auth UI, Flask backend, Stripe payments, mobile companion, Heroku deploy scripts, marketing landing page, older feature docs. Not shipped in v1; revisit for Paid Beta milestone. |
| `backups/` | Local Excel backups the app writes |

## Building the .exe

Friends don't install Python. Ship them a single `.exe` built with
PyInstaller from [`wordcounter.spec`](wordcounter.spec):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pyinstaller --noconfirm wordcounter.spec
```

The output is `dist\WordCounterPro.exe` (single file, windowed, no
console). Test it locally, then hand out the `.exe` along with
[`INSTALL.md`](INSTALL.md).

Before cutting a build for distribution:

- Bump `APP_VERSION` at the top of [`wordcounter.py`](wordcounter.py).
- Set `FEEDBACK_EMAIL` to a real inbox.
- Run once locally and click through the first-run wizard to confirm
  nothing regressed.

## Milestone

Current milestone: **Validate** - Windows-only, free, shipped to 3-5 friends
for 2 weeks of real feedback. Next milestone (Public Beta) adds a landing
page, broader allowlist, and optional cloud sync. Paid v1 comes after that.

## Notes

- The Polymarket market-making bot that previously lived in this folder
  has been split out to `C:\Users\1rahu\OneDrive\Polymarket Bot` and has
  its own git repo.
