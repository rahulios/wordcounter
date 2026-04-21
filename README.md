# Word Counter Pro

## What it is

Word Counter Pro is a private, local desktop writing-productivity tracker
for macOS and Windows. It sits quietly in the background while you write
in Obsidian, Microsoft Word, Scrivener, Ulysses, iA Writer, Evernote,
Notepad++, and friends — and keeps a daily log of **how many words you
wrote**, nothing else. No cloud. No account. No telemetry.

## Who it's for

- Writers who want a reliable, at-a-glance view of daily output.
- Students and researchers grinding on long-form drafts (theses,
  dissertations, papers) who care about streaks and cumulative progress.
- Anyone who wants a writing-habit tracker that respects their keyboard
  and doesn't upload anything.

Heads up: this version tracks **desktop writing apps only**. If you write
primarily in Google Docs, Notion web, or other browser-based tools, they
aren't counted in v1.

## What you get

**Tracking**
- Live word count and words-per-minute while you write.
- Session timer that only runs inside your chosen writing apps.
- Automatic daily totals — open the app tomorrow and today's number is
  already waiting.

**Goals & motivation**
- A daily word-count goal with a live progress bar.
- Writing streaks so not-writing-today has a visible cost.
- Achievements as you hit milestones.

**Analytics**
- A dashboard with weekly and monthly charts.
- "Best hour of day" and "most productive day of the week" insights.
- Longest streak, average session length, WPM trends.

**Data ownership**
- Everything is stored locally in a plain Excel workbook you can open in
  Excel, Numbers, or LibreOffice.
- One-click CSV or JSON export.
- Automatic rolling backups inside your user app-data folder.
- No cloud uploads. No account. No telemetry. No network calls.

**Quality-of-life**
- Light and dark mode.
- Keyboard shortcuts for the common actions.
- Friendly first-run setup wizard.
- Optional launch-on-login, so tracking starts when you do.

## How privacy actually works

Word Counter Pro is **not** a general keystroke logger. It works by
watching which app is in the foreground:

- A foreground-app hook notices which app you just clicked into.
- The keyboard listener **only runs while one of your allowlisted
  writing apps is focused**. When you switch to Chrome, Slack, your
  password manager, or anything else, the listener is stopped; any key
  events still in flight before it unwinds are ignored and never
  counted, logged, or stored.
- Only aggregate counts (words, duration, WPM) are saved to disk. The
  partial word you're in the middle of typing lives in a short in-memory
  buffer that's cleared on every word boundary, pause, stop, and
  app-switch.
- There are no cloud uploads, no telemetry, and no network calls in v1.

The source is open — audit `AppFocusManager`, `FocusWatcher`, and
`WordDetector` in [`wordcounter.py`](wordcounter.py) to verify every
claim.

## Status

Current milestone: **Validate** — free, shared with a handful of friends
for ~2 weeks of real feedback on macOS + Windows. A **Public Beta** with
a landing page and broader allowlist is next, followed by a **Paid v1**.

---

# For developers

Built with Tkinter + `pynput`. Windows uses `pywin32` + SetWinEventHook
for focus tracking; macOS uses PyObjC + NSWorkspace notifications.

## Privacy model

This app is **not** a general keystroke logger. By design:

- A foreground-app hook watches which app is focused.
- The keyboard listener **only runs while an allowlisted writing app is
  focused**. When you switch to Chrome, Slack, your password manager, or
  anything else, the listener is stopped; any key events still delivered
  to the process before it unwinds are ignored and never counted, logged,
  or stored.
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
| [`demo_data.py`](demo_data.py) | Generates synthetic writing history into a temp dir so you can preview the analytics dashboard without using real data |

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

## Notes

- The Polymarket market-making bot that previously lived in this folder
  has been split out to `C:\Users\1rahu\OneDrive\Polymarket Bot` and has
  its own git repo.
