# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller build spec for WordCounter Pro (Windows-only).
#
# Usage (from the project root with the venv active and PyInstaller installed):
#     pyinstaller --noconfirm wordcounter.spec
#
# Output:
#     dist\WordCounterPro.exe  (single-file, windowed build)
#
# To install PyInstaller once:
#     pip install pyinstaller
#
# Notes:
#   * This is a "windowed" build (console=False) so friends don't see a
#     terminal window when they launch the .exe.
#   * hiddenimports cover libraries that PyInstaller sometimes fails to
#     auto-detect (matplotlib Tk backend, pynput backends, pywin32).
#   * Data files are intentionally minimal: the app creates its own
#     %APPDATA%\WordCounterPro\ directory at runtime for config / data / logs.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files


block_cipher = None


hiddenimports = []
hiddenimports += collect_submodules("pynput")
hiddenimports += collect_submodules("matplotlib.backends")
hiddenimports += [
    "pkg_resources.py2_warn",
    "win32gui",
    "win32process",
    "win32api",
    "pywintypes",
    "pythoncom",
    "winreg",
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
        # Keep the binary lean: we don't ship tests / docs / unused GUI toolkits.
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="WordCounterPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/wordcounter.ico",  # add when an .ico file is available
)
