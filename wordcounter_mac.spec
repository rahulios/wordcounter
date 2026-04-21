# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller build spec for WordCounter Pro (macOS only).
#
# Must be built on a real Mac. Produces a double-clickable .app bundle:
#     dist/WordCounterPro.app
#
# Usage (from the project root on the Mac, inside a venv):
#     pip install -r requirements.txt
#     pyinstaller --noconfirm wordcounter_mac.spec
#
# Notes:
#   * This produces an unsigned, unnotarized .app. On another Mac the user
#     has to right-click -> Open the first time (see INSTALL.md / BUILD_MAC.md).
#   * hiddenimports include the PyObjC framework modules used by the macOS
#     FocusWatcher and the permission probes.
#   * info_plist contains the usage-description strings macOS surfaces in the
#     Accessibility / Input Monitoring prompts.
#   * target_arch is left None so the build matches the host (arm64 on Apple
#     Silicon Macs, x86_64 on Intel Macs). Use 'universal2' only with a
#     properly configured universal Python.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files


block_cipher = None


hiddenimports = []
hiddenimports += collect_submodules("pynput")
hiddenimports += collect_submodules("matplotlib.backends")
hiddenimports += [
    # PyObjC frameworks the app imports lazily at runtime.
    "AppKit",
    "Foundation",
    "objc",
    "Quartz",
    "ApplicationServices",
    # Other libs PyInstaller sometimes misses.
    "seaborn",
    "openpyxl",
    "sv_ttk",
]


# sv-ttk ships its tcl theme files as package data; PyInstaller needs
# them bundled or sv_ttk.set_theme() will raise at runtime.
datas = []
datas += collect_data_files("sv_ttk")


a = Analysis(
    ["wordcounter.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tests",
        "tkinter.test",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "wx",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WordCounterPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/wordcounter.icns",  # add when an .icns file is available
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="WordCounterPro",
)


app = BUNDLE(
    coll,
    name="WordCounterPro.app",
    icon=None,  # swap in "assets/wordcounter.icns" when available
    bundle_identifier="com.wordcounterpro.app",
    info_plist={
        "CFBundleName": "WordCounterPro",
        "CFBundleDisplayName": "WordCounter Pro",
        "CFBundleExecutable": "WordCounterPro",
        "CFBundleIdentifier": "com.wordcounterpro.app",
        "CFBundleShortVersionString": "0.2.0",
        "CFBundleVersion": "0.2.0",
        "CFBundlePackageType": "APPL",
        # Regular foreground app (Dock icon + menu bar); not a menu-bar-only
        # utility. Set LSUIElement=True later if we ship a tray-only mode.
        "LSUIElement": False,
        "NSHighResolutionCapable": True,
        "NSSupportsAutomaticGraphicsSwitching": True,
        # Usage strings. These are the exact texts macOS shows in the prompt
        # dialog the first time the app triggers a protected API.
        "NSAccessibilityUsageDescription": (
            "WordCounter uses Accessibility to detect which app is focused, "
            "so it only counts keystrokes while you're in one of your "
            "allowlisted writing apps."
        ),
        # Unofficial / non-prompting but documented in Apple headers; we keep
        # it here for completeness in case Apple starts surfacing it.
        "NSAppleEventsUsageDescription": (
            "WordCounter uses system events to detect which app is focused."
        ),
    },
)
