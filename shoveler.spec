# shoveler.spec
#
# Build with:  uv run pyinstaller shoveler.spec
# Output:      dist/Shoveler/   (--onedir, recommended)
#
# Why --onedir and not --onefile:
#   --onefile extracts everything to a temp directory on every launch,
#   making startup slow. --onedir is faster and easier to debug.
#   Distribute the dist/DuckDB Workbench/ folder as a zip.

from PyInstaller.utils.hooks import collect_all

# collect_all picks up:
#   - the duckdb Python package
#   - _duckdb.pyd (the compiled extension, which lives outside the package dir)
#   - any data files shipped with duckdb
# Without this, the packaged app fails at runtime with an ImportError on _duckdb.
duckdb_datas, duckdb_binaries, duckdb_hiddenimports = collect_all("duckdb")
app_icon = "src/shoveler/assets/shoveler.ico"

a = Analysis(
    ["src/shoveler/__main__.py"],
    pathex=[],
    binaries=duckdb_binaries,
    datas=duckdb_datas + [(app_icon, "shoveler/assets")],
    hiddenimports=duckdb_hiddenimports,
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
    [],
    exclude_binaries=True,  # required for COLLECT (onedir mode)
    name="Shoveler",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon=app_icon,
    console=False,  # no console window — same effect as gui-scripts in pyproject.toml
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Shoveler",
)
