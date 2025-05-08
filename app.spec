# app.spec

# Required PyInstaller imports
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.building.datastruct import TOC
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.building.datastruct import Tree
import os
import sys

# Paths
project_path = os.path.abspath(".")
icon_path_win = os.path.join(project_path, "assets/icon.ico")
icon_path_mac = os.path.join(project_path, "assets/icon.icns")

# Pick icon based on platform
icon_file = icon_path_win if sys.platform.startswith("win") else icon_path_mac

a = Analysis(
    ['app.py'],
    pathex=[project_path],
    binaries=[],
    datas=[
        ('assets/example.csv', 'assets'),
        ('assets/example.yaml', 'assets'),
        ('docs/annotator_guide.pdf', 'docs'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ReportAnnotationGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=icon_file
)