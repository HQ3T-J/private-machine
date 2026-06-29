# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:\\临时文件夹\\standupsync_desktop\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('E:\\临时文件夹\\standupsync_desktop/theme.py', '.'), ('E:\\临时文件夹\\standupsync_desktop/widgets.py', '.'), ('E:\\临时文件夹\\standupsync_desktop/api_client.py', '.'), ('E:\\临时文件夹\\standupsync_desktop/app.py', '.'), ('E:\\临时文件夹\\standupsync_desktop/views', 'views')],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'theme', 'widgets', 'api_client', 'app', 'views', 'views.login_view', 'views.home_view', 'views.meeting_room_view', 'views.ai_result_view', 'views.todo_view', 'views.dashboard_view', 'views.team_view', 'views.settings_view'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],
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
    name='StandupSync',
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
