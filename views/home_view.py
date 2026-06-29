"""站会首页 - StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt


class HomeView(QWidget):
    """站会首页"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "站会"
        self.setStyleSheet(self._base_style())
        self._setup_ui()

    def _base_style(self):
        return """
            QWidget {
                background-color: #1A1A2E;
                color: #E0E0E0;
            }
            QLabel#page_title {
                font-size: 20px;
                font-weight: bold;
                color: #FFFFFF;
                padding-bottom: 8px;
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
        title_label = QLabel(self.title)
        title_label.setObjectName("page_title")
        layout.addWidget(title_label)

        # ---- 第一行: 2 张并排卡片 ----
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        # 卡片1: 进行中的站会
        active_card = self._create_active_card()
        cards_row.addWidget(active_card, 1)

        # 卡片2: 快速统计
        stats_card = self._create_stats_card()
        cards_row.addWidget(stats_card, 1)

        layout.addLayout(cards_row)

        # ---- 第二行: 历史站会列表 ----
        history_label = QLabel("历史站会")
        history_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #CCCCCC;")
        layout.addWidget(history_label)

        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)

    def _card_style(self):
        return """
            background-color: #16213E;
            border: 1px solid #0F3460;
            border-radius: 10px;
            padding: 18px;
        """

    def _create_active_card(self):
        card = QFrame()
        card.setStyleSheet(self._card_style())
        card.setMinimumHeight(120)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(8)

        title_lbl = QLabel("📋 进行中的站会")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        cl.addWidget(title_lbl)

        info_lbl = QLabel("Sprint#12 · 第3次")
        info_lbl.setStyleSheet("font-size: 13px; color: #AAAAAA;")
        cl.addWidget(info_lbl)

        bottom_row = QHBoxLayout()
        timer_lbl = QLabel("⏱ 剩余 08:42")
        timer_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A90D9;")
        bottom_row.addWidget(timer_lbl)

        bottom_row.addStretch()

        enter_btn = QPushButton("进入站会 →")
        enter_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5BA0E9;
            }
        """)
        enter_btn.setCursor(Qt.PointingHandCursor)
        bottom_row.addWidget(enter_btn)

        cl.addLayout(bottom_row)
        return card

    def _create_stats_card(self):
        card = QFrame()
        card.setStyleSheet(self._card_style())
        card.setMinimumHeight(120)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(8)

        title_lbl = QLabel("📊 快速统计")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        cl.addWidget(title_lbl)

        stats = [
            ("本月", "12次站会"),
            ("出勤率", "87%"),
            ("完成率", "73%"),
            ("阻碍", "3个"),
        ]
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for i, (label, value) in enumerate(stats):
            item_widget = QWidget()
            iv = QVBoxLayout(item_widget)
            iv.setContentsMargins(0, 0, 0, 0)
            iv.setSpacing(2)

            val_lbl = QLabel(value)
            val_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A90D9;")
            val_lbl.setAlignment(Qt.AlignCenter)
            iv.addWidget(val_lbl)

            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; color: #888888;")
            lbl.setAlignment(Qt.AlignCenter)
            iv.addWidget(lbl)

            (row1 if i < 2 else row2).addWidget(item_widget)

        cl.addLayout(row1)
        cl.addLayout(row2)
        return card

    def _setup_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "Sprint", "出勤率", "完成率", "阻碍", "操作"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 8px;
                gridline-color: #0F3460;
                color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 6px 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #0F3460;
                color: #CCCCCC;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:alternate {
                background-color: #1A1A3E;
            }
        """)

        # 5 行占位数据
        placeholder_data = [
            ("2024-06-28", "Sprint#12", "87%", "73%", "3", ""),
            ("2024-06-27", "Sprint#12", "92%", "80%", "1", ""),
            ("2024-06-26", "Sprint#12", "85%", "68%", "2", ""),
            ("2024-06-25", "Sprint#11", "90%", "75%", "1", ""),
            ("2024-06-24", "Sprint#11", "88%", "71%", "0", ""),
        ]

        self.table.setRowCount(len(placeholder_data))
        for row_idx, (date, sprint, attendance, completion, blockers, _) in enumerate(placeholder_data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(date))
            self.table.setItem(row_idx, 1, QTableWidgetItem(sprint))
            self.table.setItem(row_idx, 2, QTableWidgetItem(attendance))
            self.table.setItem(row_idx, 3, QTableWidgetItem(completion))
            self.table.setItem(row_idx, 4, QTableWidgetItem(blockers))

            view_btn = QPushButton("查看")
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #4A90D9;
                    border: 1px solid #4A90D9;
                    border-radius: 4px;
                    padding: 3px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(74, 144, 217, 0.2);
                }
            """)
            view_btn.setCursor(Qt.PointingHandCursor)
            self.table.setCellWidget(row_idx, 5, view_btn)
