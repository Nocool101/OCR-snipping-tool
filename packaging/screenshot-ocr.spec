# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：把工具打成单文件 exe（dist/screenshot-ocr.exe）。

用 build.ps1 运行；也可手动：
    python -m PyInstaller --noconfirm --clean packaging/screenshot-ocr.spec
"""

from pathlib import Path

ROOT = Path(SPECPATH).parent
ICON = ROOT / "assets" / "app.ico"

a = Analysis(
    [str(ROOT / "launcher.pyw")],
    pathex=[str(ROOT)],
    binaries=[],
    # app.ico 随包分发，运行时可被 icon.app_icon() 读到（冻结后位于 _MEIPASS/assets）。
    datas=[(str(ICON), "assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="screenshot-ocr",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON),
)
