# WordCounter Pro — Install & Use

Thanks for helping us validate this. This doc gets you from zero to "it's
counting my words" in about two minutes.

## What this is

WordCounter Pro is a small Windows desktop app that counts the words you
type **only while you are using one of your writing apps** (Microsoft
Word, Obsidian, Evernote, Scrivener, Notepad++, Typora, etc.). It saves
daily totals locally to an Excel file so you can see your streak.

It is **not** a general keystroke logger:
- The keyboard listener is literally stopped whenever the focused window
  is anything other than an allowlisted writing app.
- No words, sentences, or document contents are ever stored.
- No network calls. No telemetry. Everything stays on your machine.

## System requirements

- Windows 10 or Windows 11
- ~50 MB free disk space

## Install

1. Download `WordCounterPro.exe`.
2. Put it somewhere permanent like `C:\Users\<you>\Apps\WordCounterPro\`.
3. Double-click it.
4. Windows SmartScreen may show a "Windows protected your PC" dialog the
   first time (the build isn't code-signed yet during the friends
   pilot). Click **More info** → **Run anyway**.
5. A Welcome wizard will appear.
   - Screen 1: confirm you understand the privacy model.
   - Screen 2: pick which of your writing apps should be tracked. You
     can edit this list any time via `Tools → Writing Apps...`.
   - Optional: check "Launch on Windows startup" if you want it always
     running in the background.

## Day-to-day use

1. Launch the app.
2. Click **Start Recording**.
3. Switch to your writing app (Word, Obsidian, etc.) and write.
4. The status bar at the bottom of WordCounter will show:
   - `Recording - Obsidian` while you're writing in a tracked app.
   - `Armed - waiting...` while your focus is elsewhere (nothing is
     captured during this state — the listener is actually stopped).
5. At the end of your session click **Stop** (or just close the app; it
   will prompt you to save).

Your history lives in the Analytics dashboard (`View → Analytics
Dashboard`) and in the underlying Excel file at:

`%APPDATA%\WordCounterPro\WordCountData.xlsx`

## Uninstall

WordCounter Pro is a single `.exe` with no installer. To remove it:

1. Close the app from the tray / close the window.
2. Delete `WordCounterPro.exe`.
3. (Optional) Delete your data directory: `%APPDATA%\WordCounterPro\`.
4. (Optional) Remove the Windows startup entry, if you enabled it:
   - `Win + R` → type `regedit` → Enter.
   - Navigate to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`.
   - Delete the `WordCounterPro` value.

## Troubleshooting

**The app doesn't count anything.**
- Check the status bar. If it shows `Armed - waiting...` when you're
  writing, your writing app probably isn't on the allowlist.
- Open `Tools → Writing Apps...`, click **Refresh**, and confirm the
  process name of the focused app. Add it if missing. Hit **Save**.
- Some apps (like modern Evernote) are UWP-style wrappers. If the
  reported process name looks like `ApplicationFrameHost.exe`, click
  directly into the writing window first and hit Refresh.

**The app won't start / crashed.**
- Crash reports are written to `%APPDATA%\WordCounterPro\crashes\`.
- On next launch WordCounter will offer to open the folder.
- You can also use `Help → Send Feedback...` to email us the logs.

## Feedback

We'd love anything at all — bugs, wins, "meh I stopped using it after a
day because X". Two ways to reach us:

- In-app: **Help → Send Feedback...** (pre-fills an email with the app
  version and your OS).
- Direct: reply to whoever sent you this file.

There will also be a short (5-question) Google Form sent around the end
of week 1 and again at end of week 2.

Thanks for helping!
