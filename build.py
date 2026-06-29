# StandupSync Desktop — PyInstaller 打包脚本
# 运行: python build.py

import PyInstaller.__main__
import os

root = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(root, 'main.py'),
    '--name=StandupSync',
    '--onefile',
    '--windowed',
    '--clean',
    '--noconfirm',
    f'--add-data={root}/theme.py{os.pathsep}.',
    f'--add-data={root}/widgets.py{os.pathsep}.',
    f'--add-data={root}/api_client.py{os.pathsep}.',
    f'--add-data={root}/app.py{os.pathsep}.',
    f'--add-data={root}/views{os.pathsep}views',
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtGui',
    '--hidden-import=PySide6.QtWidgets',
    '--hidden-import=theme',
    '--hidden-import=widgets',
    '--hidden-import=api_client',
    '--hidden-import=app',
    '--hidden-import=views',
    '--hidden-import=views.login_view',
    '--hidden-import=views.home_view',
    '--hidden-import=views.meeting_room_view',
    '--hidden-import=views.ai_result_view',
    '--hidden-import=views.todo_view',
    '--hidden-import=views.dashboard_view',
    '--hidden-import=views.team_view',
    '--hidden-import=views.settings_view',
    '--exclude-module=tkinter',
    '--exclude-module=matplotlib',
    '--exclude-module=numpy',
])
