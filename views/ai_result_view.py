"""AI 纪要结果页（2×2网格）- StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt


class AIResultView(QWidget):
    """AI 纪要结果页"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "AI 纪要"
        self.setStyleSheet(self._base_style())
        self._setup_ui()

    def _base_style(self):
        return """
            QWidget {
                background-color: #1A1A2E;
                color: #E0E0E0;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #CCCCCC;
                border: 1px solid #0F3460;
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 18px;
                background-color: #16213E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """

    def activate(self):
        """页面显示时调用"""
        pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ---- 页面标题 ----
        title_label = QLabel("🤖 AI 站会纪要")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title_label)

        # ---- 2×2 网格 ----
        grid = QVBoxLayout()
        grid.setSpacing(14)

        # 第一行
        row1 = QHBoxLayout()
        row1.setSpacing(14)

        yesterday_group = self._create_list_group("✅ 昨日完成", [
            "张三：完成登录模块重构，修复 3 个遗留 bug",
            "李四：后端 API 联调完成，接口文档更新",
            "王五：权限管理模块开发完成 80%",
            "赵六：数据库迁移脚本编写",
            "钱七：前端 CI/CD 流水线搭建",
        ])
        row1.addWidget(yesterday_group, 1)

        today_group = self._create_list_group("📋 今日计划", [
            "张三：开始权限管理模块开发",
            "李四：Code Review + 性能优化",
            "王五：权限管理剩余 20% + 单元测试",
            "赵六：部署数据库迁移到预发环境",
            "钱七：前端打包优化 + E2E 测试",
        ])
        row1.addWidget(today_group, 1)

        grid.addLayout(row1)

        # 第二行
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        blockers_group = self._create_blockers_group()
        row2.addWidget(blockers_group, 1)

        actions_group = self._create_actions_group()
        row2.addWidget(actions_group, 1)

        grid.addLayout(row2)
        layout.addLayout(grid, 1)

        # ---- 底部按钮栏 ----
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        regen_btn = QPushButton("重新生成")
        regen_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #16213E;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
        """)
        regen_btn.setCursor(Qt.PointingHandCursor)
        bottom_bar.addWidget(regen_btn)

        bottom_bar.addStretch()

        confirm_btn = QPushButton("确认并结束站会")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5BA0E9;
            }
        """)
        confirm_btn.setCursor(Qt.PointingHandCursor)
        bottom_bar.addWidget(confirm_btn)

        share_btn = QPushButton("分享")
        share_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #16213E;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
        """)
        share_btn.setCursor(Qt.PointingHandCursor)
        bottom_bar.addWidget(share_btn)

        layout.addLayout(bottom_bar)

    def _create_list_group(self, title, items):
        """创建普通列表 QGroupBox"""
        group = QGroupBox(title)
        gl = QVBoxLayout(group)
        gl.setContentsMargins(10, 14, 10, 10)

        lst = QListWidget()
        lst.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #CCCCCC;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 4px;
                border-bottom: 1px solid #0F3460;
            }
            QListWidget::item:hover {
                background-color: #1A3A5E;
                border-radius: 4px;
            }
        """)
        for item_text in items:
            lst.addItem(item_text)

        gl.addWidget(lst)
        return group

    def _create_blockers_group(self):
        """创建阻碍汇总 QGroupBox（红色背景提示）"""
        group = QGroupBox("🚧 阻碍汇总")
        gl = QVBoxLayout(group)
        gl.setContentsMargins(10, 14, 10, 10)

        lst = QListWidget()
        lst.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #CCCCCC;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 4px;
                border-bottom: 1px solid #0F3460;
                background-color: rgba(255, 77, 77, 0.08);
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 77, 77, 0.15);
            }
        """)
        blockers = [
            "🚧 李四：测试环境不稳定，阻塞联调",
            "🚧 钱七：前端打包构建时间过长（>10min）",
        ]
        for b in blockers:
            lst.addItem(b)

        gl.addWidget(lst)
        return group

    def _create_actions_group(self):
        """创建 Action Item QGroupBox（带优先级色标）"""
        group = QGroupBox("📌 Action Item")
        gl = QVBoxLayout(group)
        gl.setContentsMargins(10, 14, 10, 10)

        lst = QListWidget()
        lst.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #CCCCCC;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 4px;
                border-bottom: 1px solid #0F3460;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background-color: #1A3A5E;
            }
        """)

        actions = [
            ("🔴 高", "张三：本周五前完成权限模块开发", "#FF4D4D"),
            ("🟡 中", "赵六：周三前部署迁移脚本到预发", "#FFB84D"),
            ("🟢 低", "李四：整理接口文档并同步前端", "#4DCC4D"),
        ]
        for priority_label, text, color in actions:
            item = QListWidgetItem(f"{priority_label}  {text}")
            item.setForeground(Qt.GlobalColor.white)
            lst.addItem(item)

        gl.addWidget(lst)
        return group
