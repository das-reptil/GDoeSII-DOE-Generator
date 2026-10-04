# -*- mode: python ; coding: utf-8 -*-
import os

src_dir = os.path.abspath(os.path.join(SPECPATH, "..", "src"))

a = Analysis(
    [os.path.join(src_dir, "GDoeSII_Film_GS_Batch.py")],
    pathex=[src_dir],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="GDoeSII_Film_GS_Batch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
