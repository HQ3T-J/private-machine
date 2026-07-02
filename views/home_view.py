"""站会首页 - StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSizePolicy, QSpacerItem, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QDialogButtonBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from widgets import EmptyState


class CreateMeetingDialog(QDialog):
    """创建站会对话框"""

    def __init__(self, api_client=None, team_id=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.team_id = team_id
        self.setWindowTitle("创建新站会")
        self.setFixedSize(360, 200)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("例如: Sprint 12 每日站会")
        self._title_input.setMinimumHeight(32)
        layout.addRow("标题:", self._title_input)

        self._sprint_input = QLineEdit()
        self._sprint_input.setPlaceholderText("例如: 12")
        self._sprint_input.setMinimumHeight(32)
        layout.addRow("Sprint #:", self._sprint_input)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_create)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

        self.setStyleSheet("""
            QLineEdit { border-radius: 4px; padding: 6px 10px; font-size: 13px; }
        """)

    def _on_create(self):
        title = self._title_input.text().strip() or "每日站会"
        sprint = self._sprint_input.text().strip() or "1"
        if self.api_client and self.team_id:
            self.api_client.create_meeting(self.team_id, sprint, title)
        self.accept()


class HomeView(QWidget):
    """站会首页 —— 对接后端真实数据"""

    navigate_to_meeting = Signal(int, dict)  # meeting_id, meeting_data
    meeting_created = Signal()

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "站会"
        self._meetings = []
        self._teams = []
        self._current_team_id = None
        self._setup_ui()

    def activate(self):
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ---- 页面标题 + 操作按钮 ----
        header_row = QHBoxLayout()
        title_label = QLabel(self.title)
        title_label.setObjectName("page_title")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding-bottom: 8px;")
        header_row.addWidget(title_label)
        header_row.addStretch()

        self._team_label = QLabel("")
        self._team_label.setStyleSheet("font-size: 13px;")
        header_row.addWidget(self._team_label)

        self._team_combo = QComboBox()
        self._team_combo.setFixedWidth(160)
        self._team_combo.setStyleSheet("QComboBox{border-radius:4px;padding:2px 6px;font-size:12px;}")
        self._team_combo.currentIndexChanged.connect(self._on_team_changed)
        header_row.addWidget(self._team_combo)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("RefreshBtn")
        refresh_btn.setStyleSheet("""
            QPushButton#RefreshBtn { background: transparent; border: 1px solid #4A90D9;
                border-radius: 4px; padding: 4px 12px; font-size: 12px; color: #4A90D9; }
            QPushButton#RefreshBtn:hover { background: rgba(74,144,217,0.2); }
        """)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_data)
        header_row.addWidget(refresh_btn)

        self._create_btn = QPushButton("+ 创建站会")
        self._create_btn.setStyleSheet("""
            QPushButton { background: #52C41A; color: #FFF; border: none;
                border-radius: 4px; padding: 6px 14px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background: #45A818; }
        """)
        self._create_btn.setCursor(Qt.PointingHandCursor)
        self._create_btn.clicked.connect(self._on_create_meeting)
        header_row.addWidget(self._create_btn)
        layout.addLayout(header_row)

        # ---- 第一行: 2 张并排卡片 ----
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self._active_card = self._create_active_card()
        cards_row.addWidget(self._active_card, 1)

        self._stats_card = self._create_stats_card()
        cards_row.addWidget(self._stats_card, 1)

        layout.addLayout(cards_row)

        # ---- 第二行: 站会列表 ----
        history_label = QLabel("站会记录")
        history_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(history_label)

        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)

    def _card_style(self):
        return "border-radius: 10px; padding: 18px;"

    def _create_active_card(self):
        card = QFrame()
        card.setObjectName("StatCard")
        card.setMinimumHeight(120)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(8)

        self._active_title = QLabel("进行中的站会")
        self._active_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        cl.addWidget(self._active_title)

        self._active_info = QLabel("暂无进行中的站会")
        self._active_info.setStyleSheet("font-size: 13px;")
        cl.addWidget(self._active_info)

        bottom_row = QHBoxLayout()
        self._active_detail = QLabel("")
        self._active_detail.setStyleSheet("font-size: 14px; color: #4A90D9;")
        bottom_row.addWidget(self._active_detail)
        bottom_row.addStretch()

        self._enter_btn = QPushButton("进入站会")
        self._enter_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: #FFF; border: none;
                border-radius: 6px; padding: 6px 16px; font-size: 13px; }
            QPushButton:hover { background: #5BA0E9; }
        """)
        self._enter_btn.setCursor(Qt.PointingHandCursor)
        self._enter_btn.clicked.connect(self._on_enter_meeting)
        self._enter_btn.setVisible(False)
        bottom_row.addWidget(self._enter_btn)

        cl.addLayout(bottom_row)
        return card

    def _create_stats_card(self):
        card = QFrame()
        card.setObjectName("StatCard")
        card.setMinimumHeight(120)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(8)

        title_lbl = QLabel("快速统计")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        cl.addWidget(title_lbl)

        self._stat_labels = {}
        stats = [
            ("total", "站会", "0"),
            ("attendance", "出勤率", "--"),
            ("completion", "完成率", "--"),
            ("blockers", "阻碍", "0"),
        ]
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for i, (key, label, default) in enumerate(stats):
            w = QWidget()
            iv = QVBoxLayout(w)
            iv.setContentsMargins(0, 0, 0, 0)
            iv.setSpacing(2)
            val_lbl = QLabel(default)
            val_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A90D9;")
            val_lbl.setAlignment(Qt.AlignCenter)
            iv.addWidget(val_lbl)
            self._stat_labels[key] = val_lbl
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px;")
            lbl.setAlignment(Qt.AlignCenter)
            iv.addWidget(lbl)
            (row1 if i < 2 else row2).addWidget(w)
        cl.addLayout(row1)
        cl.addLayout(row2)
        return card

    def _setup_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "标题", "Sprint", "状态", "阻碍", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        # 表格圆角（颜色由全局QSS管理）
        self.table.setStyleSheet("QTableWidget { border-radius: 8px; }")

    def _load_data(self):
        if not self.api_client:
            return
        self._teams = self.api_client.get_teams() or []

        self._team_combo.blockSignals(True)
        self._team_combo.clear()
        for t in self._teams:
            self._team_combo.addItem(t.get("name", f"Team #{t['id']}"), t.get("id"))
        self._team_combo.blockSignals(False)

        if self._teams:
            self._current_team_id = self._team_combo.currentData() or self._teams[0].get("id")
            self._create_btn.setVisible(True)
        else:
            self._team_label.setText("(暂无团队)")
            self._current_team_id = None
            self._create_btn.setVisible(False)

        if self._current_team_id:
            self._meetings = self.api_client.get_meetings(self._current_team_id) or []
            self._refresh_table()
            self._refresh_cards()
            self._load_stats()

    def _on_team_changed(self, _idx):
        if self._team_combo.count() == 0:
            return
        self._current_team_id = self._team_combo.currentData()
        if self._current_team_id:
            self._meetings = self.api_client.get_meetings(self._current_team_id) or []
            self._refresh_table()
            self._refresh_cards()
            self._load_stats()

    def _refresh_cards(self):
        active = [m for m in self._meetings if m.get("status") == "ACTIVE"]
        created = [m for m in self._meetings if m.get("status") == "CREATED"]
        if active:
            m = active[0]
            self._active_title.setText("进行中的站会")
            title = m.get("title") or f"Sprint#{m.get('sprintNo', '?')}"
            self._active_info.setText(title)
            self._active_detail.setText("发言进行中...")
            self._enter_btn.setVisible(True)
            self._enter_btn.setProperty("meeting_id", m.get("id"))
            self._enter_btn.setProperty("meeting_data", m)
        elif created:
            m = created[0]
            self._active_title.setText("待开始的站会")
            title = m.get("title") or f"Sprint#{m.get('sprintNo', '?')}"
            self._active_info.setText(title)
            self._active_detail.setText("点击进入开始站会")
            self._enter_btn.setText("进入站会")
            self._enter_btn.setVisible(True)
            self._enter_btn.setProperty("meeting_id", m.get("id"))
            self._enter_btn.setProperty("meeting_data", m)
        else:
            self._active_title.setText("进行中的站会")
            self._active_info.setText("暂无站会")
            self._active_detail.setText("")
            self._enter_btn.setVisible(False)

    def _load_stats(self):
        if not self._current_team_id or not self.api_client:
            return
        summary = self.api_client.get_dashboard_summary(self._current_team_id) or {}
        self._stat_labels["total"].setText(str(summary.get("totalMeetings", 0)))
        rate = summary.get("avgAttendanceRate", 0)
        self._stat_labels["attendance"].setText(
            f"{int(rate * 100)}%" if isinstance(rate, float) and rate <= 1 else f"{rate}%")
        cr = summary.get("completionRate", 0)
        self._stat_labels["completion"].setText(
            f"{int(cr * 100)}%" if isinstance(cr, float) and cr <= 1 else f"{cr}%")
        self._stat_labels["blockers"].setText(str(summary.get("activeBlockers", 0)))

    def _refresh_table(self):
        self.table.setRowCount(len(self._meetings))
        for row_idx, m in enumerate(self._meetings):
            date = m.get("createdAt", "")[:10] if m.get("createdAt") else ""
            self.table.setItem(row_idx, 0, QTableWidgetItem(date))
            title = m.get("title") or f"Sprint#{m.get('sprintNo', '?')}"
            self.table.setItem(row_idx, 1, QTableWidgetItem(title))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"Sprint#{m.get('sprintNo', '')}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(m.get("status", "")))
            self.table.setItem(row_idx, 4, QTableWidgetItem("-"))

            btn_row = QHBoxLayout()
            btn_row.setSpacing(4)
            btn_row.setContentsMargins(2, 2, 2, 2)

            if m.get("status") in ("ACTIVE", "CREATED"):
                enter_sm = QPushButton("进入")
                enter_sm.setFixedHeight(26)
                enter_sm.setStyleSheet("""
                    QPushButton { background: #4A90D9; color: #FFF; border: none;
                        border-radius: 3px; padding: 4px 12px; font-size: 12px; }
                    QPushButton:hover { background: #5BA0E9; }
                """)
                enter_sm.setCursor(Qt.PointingHandCursor)
                mid = m.get("id")
                md = m
                enter_sm.clicked.connect(lambda checked=False, mid=mid, md=md: self._enter_meeting(mid, md))
                btn_row.addWidget(enter_sm)

            view_btn = QPushButton("查看")
            view_btn.setFixedHeight(26)
            view_btn.setStyleSheet("""
                QPushButton { background: transparent; color: #4A90D9;
                    border: 1px solid #4A90D9; border-radius: 3px;
                    padding: 4px 12px; font-size: 12px; }
                QPushButton:hover { background: rgba(74,144,217,0.2); }
            """)
            view_btn.setCursor(Qt.PointingHandCursor)
            mid = m.get("id")
            md = m
            view_btn.clicked.connect(lambda checked=False, mid=mid, md=md: self._on_view_meeting(mid, md))
            btn_row.addWidget(view_btn)

            btn_row.addStretch()
            wrapper = QWidget()
            wrapper.setStyleSheet("background: transparent;")
            wrapper.setLayout(btn_row)
            self.table.setCellWidget(row_idx, 5, wrapper)
            self.table.setRowHeight(row_idx, 34)

    def _on_create_meeting(self):
        if not self._current_team_id:
            QMessageBox.warning(self, "提示", "请先在团队页面创建或加入一个团队")
            return
        dlg = CreateMeetingDialog(self.api_client, self._current_team_id, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
            self.meeting_created.emit()

    def _on_enter_meeting(self):
        mid = self._enter_btn.property("meeting_id")
        md = self._enter_btn.property("meeting_data")
        if mid:
            self._enter_meeting(mid, md)

    def _enter_meeting(self, meeting_id, meeting_data=None):
        # 先确保站会已开始
        if self.api_client:
            meeting = meeting_data
            if not meeting or meeting.get("status") != "ACTIVE":
                self.api_client.start_meeting(str(meeting_id))
        self.navigate_to_meeting.emit(meeting_id, meeting_data or {})

    def _on_view_meeting(self, meeting_id, meeting_data=None):
        if meeting_data and meeting_data.get("status") == "ACTIVE":
            self._enter_meeting(meeting_id, meeting_data)
        else:
            QMessageBox.information(self, "站会详情",
                f"站会 #{meeting_id}\n标题: {meeting_data.get('title', 'N/A') if meeting_data else 'N/A'}\n状态: {meeting_data.get('status', 'N/A') if meeting_data else 'N/A'}")
