"""站会进行中页面（三栏分屏）- StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt


class MeetingRoomView(QWidget):
    """站会进行中页面"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "站会进行中"
        self.setStyleSheet(self._base_style())
        self._setup_ui()

    def _base_style(self):
        return """
            QWidget {
                background-color: #1A1A2E;
                color: #E0E0E0;
            }
        """

    def activate(self):
        """页面显示时调用"""
        pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ---- 顶部标题栏 ----
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_label = QLabel("← 站会·Sprint#12  ⏱ 08:42")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        # 按钮组
        btn_style = """
            QPushButton {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #16213E;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
        """

        skip_btn = QPushButton("跳过此人")
        skip_btn.setStyleSheet(btn_style)
        skip_btn.setCursor(Qt.PointingHandCursor)
        top_bar.addWidget(skip_btn)

        paste_btn = QPushButton("粘贴记录")
        paste_btn.setStyleSheet(btn_style)
        paste_btn.setCursor(Qt.PointingHandCursor)
        top_bar.addWidget(paste_btn)

        ai_btn = QPushButton("AI 整理")
        ai_btn.setStyleSheet(btn_style.replace("#0F3460", "#4A90D9").replace("#1A4A7A", "#5BA0E9"))
        ai_btn.setCursor(Qt.PointingHandCursor)
        top_bar.addWidget(ai_btn)

        layout.addLayout(top_bar)

        # ---- 三栏分屏 ----
        three_col = QHBoxLayout()
        three_col.setSpacing(12)

        # 左栏: 参会成员
        left_col = self._create_member_list()
        three_col.addWidget(left_col, 1)

        # 中栏: 发言区
        center_col = self._create_speech_area()
        three_col.addWidget(center_col, 2)

        # 右栏: 已完成发言
        right_col = self._create_completed_area()
        three_col.addWidget(right_col, 1)

        layout.addLayout(three_col, 1)

        # ---- 底部提示 ----
        hint_label = QLabel("💡 Ctrl+Enter 提交发言")
        hint_label.setStyleSheet("font-size: 12px; color: #888888; padding: 4px 0;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)

    def _create_member_list(self):
        """创建左栏: 参会成员列表（210px固定宽度）"""
        container = QWidget()
        container.setFixedWidth(210)
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        member_label = QLabel("👥 参会成员")
        member_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CCCCCC;")
        cl.addWidget(member_label)

        self.member_list = QListWidget()
        self.member_list.setStyleSheet("""
            QListWidget {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 8px;
                padding: 6px;
                color: #E0E0E0;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background-color: #1A3A5E;
            }
            QListWidget::item:selected {
                background-color: #0F3460;
            }
        """)
        members = [
            "🟢 张三  已发言",
            "🟢 李四  已发言",
            "🔵 王五  发言中",
            "⚪ 赵六  等待中",
            "⚪ 钱七  等待中",
        ]
        for m in members:
            self.member_list.addItem(m)

        cl.addWidget(self.member_list, 1)

        # 拖拽排序按钮
        sort_btn = QPushButton("拖拽排序")
        sort_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #AAAAAA;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #E0E0E0;
            }
        """)
        sort_btn.setCursor(Qt.PointingHandCursor)
        cl.addWidget(sort_btn)

        return container

    def _create_speech_area(self):
        """创建中栏: 发言区（蓝色边框高亮）"""
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(10)

        # 发言者标题
        speaker_label = QLabel("🎤 王五 正在发言")
        speaker_label.setStyleSheet("""
            font-size: 16px; font-weight: bold; color: #4A90D9;
            padding: 12px;
            background-color: #16213E;
            border: 2px solid #4A90D9;
            border-radius: 8px;
        """)
        cl.addWidget(speaker_label)

        # 昨天
        yesterday_label = QLabel("✅ 昨天")
        yesterday_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #AAAAAA;")
        cl.addWidget(yesterday_label)

        self.yesterday_edit = QTextEdit()
        self.yesterday_edit.setPlaceholderText("完成了登录模块重构...")
        self.yesterday_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #4A90D9;
            }
        """)
        self.yesterday_edit.setMaximumHeight(80)
        cl.addWidget(self.yesterday_edit)

        # 今天
        today_label = QLabel("📋 今天")
        today_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #AAAAAA;")
        cl.addWidget(today_label)

        self.today_edit = QTextEdit()
        self.today_edit.setPlaceholderText("开始做权限管理模块...")
        self.today_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #4A90D9;
            }
        """)
        self.today_edit.setMaximumHeight(80)
        cl.addWidget(self.today_edit)

        # 阻碍
        blocker_label = QLabel("🚧 阻碍")
        blocker_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #AAAAAA;")
        cl.addWidget(blocker_label)

        self.blocker_edit = QTextEdit()
        self.blocker_edit.setPlaceholderText("空")
        self.blocker_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #4A90D9;
            }
        """)
        self.blocker_edit.setMaximumHeight(60)
        cl.addWidget(self.blocker_edit)

        cl.addStretch()
        return container

    def _create_completed_area(self):
        """创建右栏: 已完成发言"""
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        completed_label = QLabel("✅ 已完成发言")
        completed_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CCCCCC;")
        cl.addWidget(completed_label)

        self.completed_edit = QTextEdit()
        self.completed_edit.setReadOnly(True)
        self.completed_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 8px;
                padding: 10px;
                color: #AAAAAA;
                font-size: 12px;
            }
        """)
        completed_text = (
            "张三 ✅\n"
            "  昨天：UI调整\n"
            "  今天：权限模块\n"
            "  阻碍：无\n\n"
            "李四 ✅\n"
            "  昨天：后端联调\n"
            "  今天：Code Review\n"
            "  阻碍：测试环境不稳定"
        )
        self.completed_edit.setPlainText(completed_text)
        cl.addWidget(self.completed_edit, 1)

        return container
