# Build `WordCounterPro.app` on macOS — copy-paste guide

This is the idiot-proof step-by-step for building the macOS `.app` from
source on your own Mac. If you follow these commands in order, you will
end up with `dist/WordCounterPro.app` you can drag into `/Applications/`
or zip up and send to friends.

Must be done on an actual Mac — PyInstaller cannot cross-build `.app`
bundles from Windows.

---

## 0. What you need on the Mac (one-time)

- macOS 11 (Big Sur) or newer
- Xcode Command Line Tools (for `git`, headers, etc.)
- Python 3.10, 3.11, or 3.12 — **strongly prefer a python.org installer,
  not Homebrew's unbranded python, to avoid tkinter headaches.**

Install Xcode Command Line Tools (if not already):

```bash
xcode-select --install
```

Install Python 3.12 from python.org:
<https://www.python.org/downloads/macos/>

Verify `python3` and `pip3` are the python.org version:

```bash
which python3
python3 --version
```

You want to see something like `/Library/Frameworks/Python.framework/...`
or `/usr/local/bin/python3` (x86_64) or `/opt/homebrew/...` (arm64).

---

## 1. Get the source

If you haven't already:

```bash
cd ~
git clone https://github.com/rahulios/wordcounter.git WordCounter
cd WordCounter
```

If you already cloned it, just pull the latest:

```bash
cd ~/WordCounter
git pull origin main
```

---

## 2. Create a virtualenv + install deps

```bash
cd ~/WordCounter
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip wheel
pip install -r requirements.txt
```

That will pull in the PyObjC frameworks the Mac build needs
(`pyobjc-core`, `pyobjc-framework-Cocoa`, `...-ApplicationServices`,
`...-Quartz`) plus `pyinstaller`.

---

## 3. Smoke-test from source (optional but recommended)

Before packaging, confirm the app actually runs on your Mac:

```bash
python wordcounter.py
```

The first-run wizard should appear. Walk through the three screens,
including the macOS permissions step. When prompted by macOS, grant
Accessibility and Input Monitoring to `Python` (yes, to the Python
binary, because this is an unbundled run). Close the app.

If that worked, move on.

---

## 4. Build the `.app` bundle

```bash
pyinstaller --noconfirm wordcounter_mac.spec
```

Takes 1–3 minutes. Output:

```
dist/
  WordCounterPro.app/
    Contents/
      MacOS/WordCounterPro
      Resources/
      Info.plist
      ...
```

---

## 5. Smoke-test the bundled `.app`

```bash
open dist/WordCounterPro.app
```

macOS will block it with Gatekeeper the first time (unsigned). Close
that dialog, then:

```bash
xattr -dr com.apple.quarantine dist/WordCounterPro.app
open dist/WordCounterPro.app
```

(`xattr -dr com.apple.quarantine` strips the quarantine bit so you can
open it as if you'd built it yourself; friends who download it from you
will still see the Gatekeeper prompt once.)

When it launches, macOS will ask for **Accessibility** and **Input
Monitoring** permissions — this time they'll be for `WordCounterPro`
(not `Python`). Grant both. You may need to quit + relaunch once after
granting Input Monitoring.

Type a few words in Obsidian / Word / Notes and confirm the counter
moves.

---

## 6. Ship it to a friend

Zip the bundle — `.app` directories transport badly over most chat tools:

```bash
cd dist
zip -r WordCounterPro.app.zip WordCounterPro.app
```

Send the `.zip` along with `INSTALL.md` (from the repo root). The Mac
section of `INSTALL.md` covers the right-click-Open Gatekeeper trick and
the permission grants.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'AppKit'` during
`python wordcounter.py`.**
You're running a python without PyObjC. Double-check you activated the
venv (`source .venv/bin/activate`) and reinstalled requirements.

**`pyinstaller: command not found`.**
Same — venv not active, or `pip install -r requirements.txt` was
skipped.

**App launches but does nothing when I type.**
Input Monitoring isn't granted yet. Use `Tools → Check macOS
Permissions...` inside the app, or open **System Settings → Privacy &
Security → Input Monitoring** and toggle `WordCounterPro` on. Quit and
reopen the app.

**Gatekeeper won't let me open the .app at all, even with right-click →
Open.**
On fully-up-to-date macOS Sonoma and newer, Apple tightened this. Strip
the quarantine attribute yourself:

```bash
xattr -dr com.apple.quarantine /path/to/WordCounterPro.app
```

**Building on Apple Silicon but I want an Intel build too.**
You need a universal2 Python (python.org ships one). Then in
`wordcounter_mac.spec`, set `target_arch='universal2'` in both the
`EXE(...)` and `BUNDLE(...)` calls. Easier for v1: build on one arch
and make a note of which.

---

## Future: code signing + notarization

To get rid of the Gatekeeper warning entirely (required for real
distribution), you'd:

1. Enroll in the Apple Developer Program ($99/yr).
2. Get a `Developer ID Application` certificate.
3. Sign: `codesign --deep --force --options runtime --sign "Developer ID Application: Your Name (TEAMID)" dist/WordCounterPro.app`
4. Notarize: `xcrun notarytool submit WordCounterPro.app.zip --apple-id ... --team-id ... --password ... --wait`
5. Staple: `xcrun stapler staple dist/WordCounterPro.app`

Out of scope for the Validate milestone — friends can right-click →
Open once.
