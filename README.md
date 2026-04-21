# WordCounter

A desktop app (Windows + macOS) that tracks your writing productivity
by counting words typed in the **writing apps you care about**
(Obsidian, Microsoft Word, Evernote, Scrivener, Ulysses, iA Writer,
Notepad++, etc.) and logging daily progress to an Excel workbook with
charts, goals, and analytics.

Built with Tkinter + `pynput`. Windows uses `pywin32` + SetWinEventHook
for focus tracking; macOS uses PyObjC + NSWorkspace notifications.

## Privacy model

This app is **not** a general keystroke logger. By design:

- A foreground-app hook watches which app is focused.
- The keyboard listener is **only instantiated while an allowlisted
  writing app is focused**. When you switch to Chrome, Slack, your
  password manager, or anything else, the listener is stopped and the
  process receives zero keystrokes.
- Only aggregate word counts are persisted. The in-memory `current_word`
  buffer is short-lived and zeroed on app-switch, pause, stop, and blur.
- No cloud uploads, no telemetry, no network calls in v1.

See `AppFocusManager`, `FocusWatcher`, `_WindowsFocusWatcher`, and
`_MacFocusWatcher` in [`wordcounter.py`](wordcounter.py).

## Requirements

- Windows 10/11, or macOS 11+ (Intel or Apple Silicon)
- Python 3.10+
- Dependencies in [`requirements.txt`](requirements.txt)
  (pip picks the right platform deps via `sys_platform` markers)

## Setup

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\wordcounter.py
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python wordcounter.py
```

On macOS, grant **Accessibility** and **Input Monitoring** to the
Python binary when the OS prompts (or to `WordCounterPro` after
bundling). See [`BUILD_MAC.md`](BUILD_MAC.md).

## Default allowlist

First-run wizard lets you confirm / edit. Platform-specific defaults:

**Windows** (matched on lowercase `*.exe`):
- `winword.exe`, `obsidian.exe`, `evernote.exe`, `scrivener.exe`,
- `notepad.exe`, `notepad++.exe`, `sublime_text.exe`, `typora.exe`,
- `wordpad.exe`, `onenote.exe`.

**macOS** (matched on lowercase `localizedName`):
- `microsoft word`, `obsidian`, `evernote`, `scrivener`, `ulysses`,
- `ia writer`, `notes`, `textedit`, `bbedit`, `sublime text`, `typora`,
- `bear`, `logseq`.

Browser-based writing (Google Docs, Notion web, Substack) is **not**
tracked in v1.

## Data directory

By default, config, Excel data, logs, and backups are stored under:

- Windows: `%APPDATA%\WordCounterPro\`
- macOS: `~/Library/Application Support/WordCounterPro/`

Override for development or tests:

```powershell
# Windows
$env:WORDCOUNTER_DATA_DIR = "C:\path\to\folder"
python .\wordcounter.py
```

```bash
# macOS
WORDCOUNTER_DATA_DIR=/tmp/wc python wordcounter.py
```

## Project layout

| File / folder | Purpose |
| --- | --- |
| [`wordcounter.py`](wordcounter.py) | Single-file main app (cross-platform) |
| [`wordcounter.spec`](wordcounter.spec) | PyInstaller spec for the Windows `.exe` |
| [`wordcounter_mac.spec`](wordcounter_mac.spec) | PyInstaller spec for the macOS `.app` bundle |
| [`requirements.txt`](requirements.txt) | Runtime + build deps (platform-gated) |
| [`INSTALL.md`](INSTALL.md) | End-user install guide (Windows + macOS) |
| [`BUILD_MAC.md`](BUILD_MAC.md) | Copy-paste build instructions for the macOS `.app` |
| [`FEEDBACK_FORM.md`](FEEDBACK_FORM.md) | Pilot feedback form spec |
| [`archive/old_versions/`](archive/old_versions/) | Older dated `wordcounter *.py` snapshots |
| [`archive/product-infra-2025/`](archive/product-infra-2025/) | Parked v0 cloud / auth / backend / payments / mobile code |

## Building

### Windows `.exe`

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pyinstaller --noconfirm wordcounter.spec
```

Output: `dist\WordCounterPro.exe` (single-file, windowed).

### macOS `.app`

Must be done on a real Mac. Full walkthrough:
[`BUILD_MAC.md`](BUILD_MAC.md). TL;DR:

```bash
source .venv/bin/activate
pip install -r requirements.txt
pyinstaller --noconfirm wordcounter_mac.spec
```

Output: `dist/WordCounterPro.app`.

Before cutting a build for distribution:

- Bump `APP_VERSION` at the top of [`wordcounter.py`](wordcounter.py).
- Set `FEEDBACK_EMAIL` to a real inbox.
- Run once locally and click through the first-run wizard to confirm
  nothing regressed.

## Milestone

Current milestone: **Validate** - Windows + macOS, free, shipped to
3-5 friends for ~2 weeks of real feedback. Next milestone
(**Public Beta**) adds a landing page, broader allowlist, and optional
cloud sync. **Paid v1** comes after that.

## Notes

- The Polymarket market-making bot that previously lived in this folder
  has been split out to `C:\Users\1rahu\OneDrive\Polymarket Bot` and has
  its own git repo.
