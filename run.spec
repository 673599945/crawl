# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 修改获取项目根目录的方式
ROOT_DIR = os.path.abspath('D:/Project/crawl/')
print(f"ROOT_DIR: {ROOT_DIR}")

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        (os.path.join(ROOT_DIR, 'core'), 'core'),
        (os.path.join(ROOT_DIR, 'ui'), 'ui'),
        (os.path.join(ROOT_DIR, 'spider_cache'), 'spider_cache'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'qfluentwidgets',
        'PyQt6.sip',
        'core.handler',
        'core.requester',
        'core.spiders',
        'core.utils',
        'ui.mainwindow',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='CRAWL',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CRAWL',
)

# macOS 特定配置
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='CRAWL.app',
        icon=None,
        bundle_identifier=None,
        info_plist={
            'NSHighResolutionCapable': 'True',
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [],
            'LSMinimumSystemVersion': '10.13.0',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
        },
    )
