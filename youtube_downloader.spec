# -*- mode: python ; coding: utf-8 -*-

import os

ffmpeg_bin = os.path.join(SPECPATH, "build", "ffmpeg", "bin")
ffmpeg_datas = [
    (os.path.join(ffmpeg_bin, filename), "ffmpeg")
    for filename in os.listdir(ffmpeg_bin)
    if os.path.isfile(os.path.join(ffmpeg_bin, filename))
]
a = Analysis(
    ["youtube_downloader.py"],
    pathex=[],
    binaries=[],
    datas=ffmpeg_datas,
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
    a.binaries,
    a.datas,
    [],
    name='youtube_downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
