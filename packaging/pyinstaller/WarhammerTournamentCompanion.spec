# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

project_root = Path(SPECPATH).parents[1]
src_dir = project_root / "src"

datas = collect_data_files(
    "warhammer_companion",
    includes=[
        "catalog_assets/*.svg",
        "py.typed",
        "web/static/*.css",
        "web/templates/*.html",
    ],
)

a = Analysis(
    [str(src_dir / "warhammer_companion" / "desktop" / "app.py")],
    pathex=[str(project_root), str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "warhammer_companion.desktop.app",
        "warhammer_companion.desktop.main_window",
        "warhammer_companion.desktop.screens.heatmap",
        "warhammer_companion.desktop.screens.los_checker",
        "warhammer_companion.desktop.screens.map_data",
        "warhammer_companion.desktop.screens.settings",
        "warhammer_companion.desktop.screens.viewer",
    ],
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
    name="WarhammerTournamentCompanion",
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
    name="WarhammerTournamentCompanion",
)
