# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller build spec for the Medical Laboratory Management System
# desktop application.
#
# Build with (on a Windows machine, inside the project's venv):
#
#     pyinstaller medical_lab.spec
#
# Output: dist/MedicalLaboratory/MedicalLaboratory.exe  (onedir build)
#
# Onedir (not onefile) is used deliberately: onefile re-extracts the
# whole bundle to a temp folder on every launch, which is slower and
# makes the "instant native app" feel worse. Onedir starts faster and
# is what the Inno Setup script (installer/medlab_installer.iss) expects.

import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = [
    ("app/templates", "app/templates"),
    ("app/static", "app/static"),
    ("assets/medical_lab.ico", "assets"),
]

hiddenimports = [
    "webview",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "flask",
    "flask_sqlalchemy",
    "flask_login",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "werkzeug",
    "werkzeug.serving",
    "reportlab",
    "reportlab.pdfgen",
    "reportlab.lib",
]

# Pull in pywebview's full data/binary set (it ships some platform
# glue files that PyInstaller's static analysis alone can miss).
pywebview_datas, pywebview_binaries, pywebview_hidden = collect_all("webview")
datas += pywebview_datas
hiddenimports += pywebview_hidden

a = Analysis(
    ["desktop_launcher.py"],
    pathex=[],
    binaries=pywebview_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "test", "unittest"],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MedicalLaboratory",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # console=False + windowed removes any console/terminal window
    # (Part 82: "Do not show a command prompt window to the customer").
    console=False,
    windowed=True,
    icon="assets/medical_lab.ico",
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipped_data,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MedicalLaboratory",
)
