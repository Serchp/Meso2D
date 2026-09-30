# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Meso2d.py'],
    pathex=[],
    binaries=[
        ('C:/Users/48560330Q/AppData/Local/miniconda3/Library/bin/ffi.dll', '.'),
        ('C:/Users/48560330Q/AppData/Local/miniconda3/Library/bin/ffi-8.dll', '.'),
        ('C:/Users/48560330Q/AppData/Local/miniconda3/Library/bin/libmpdec-4.dll', '.'),
    ],
    datas=[('docs', 'docs')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Meso2d',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Meso2d',
)
