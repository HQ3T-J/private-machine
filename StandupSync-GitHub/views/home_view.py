"""站会首页 - StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSizePolicy, QSpacerItem, QDialog, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QMessageBox, QDateEdit,
)
from PySide6.QtCore import QDate, Qt, Signal, QThread
from PySide6.QtGui import QBrush, QColor


class MeetingLoaderThread(QThread):
    """后台线程加载会议列表"""
    load_finished = Signal(list)
    
    def __init__(self, api_client, team_id):
        super().__init__()
        self.api_client = api_client
        self.team_id = team_id
    
    def run(self):
        try:
            if self.api_client:
                meetings = self.api_client.get_meetings(self.team_id)
            else:
                meetings = self._get_stub_meetings()
            self.load_finished.emit(meetings)
        except Exception as e:
            print(f"Failed to load meetings: {e}")
            self.load_finished.emit(self._get_stub_meetings())
    
    def _get_stub_meetings(self):
        return [
            {"id": "1", "date": "06-25", "sprint": "Sprint #12", "title": "每日站会", "status": "ended", "attendance": "4/5", "completion": "80%", "blockers": 2},
            {"id": "2", "date": "06-26", "sprint": "Sprint #12", "title": "每日站会", "status": "ended", "attendance": "5/5", "completion": "85%", "blockers": 1},
        ]


class HomeView(QWidget):
    """站会首页"""

    meeting_created = Signal(dict)
    meeting_enter = Signal(str)
    view_meeting = Signal(str)

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._current_team_id = "1"
        self.title = "站会"
        self.setStyleSheet(self._base_style())
        self._setup_ui()

    def set_team_id(self, team_id: str):
        self._current_team_id = team_id
        self.activate()

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
        self._load_meetings()
        self._update_stats()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        top_section = QHBoxLayout()

        title_label = QLabel(self.title)
        title_label.setObjectName("page_title")
        top_section.addWidget(title_label)

        top_section.addStretch()

        self._btn_new_meeting = QPushButton("+ 新建站会")
        self._btn_new_meeting.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5BA0E9;
            }
        """)
        self._btn_new_meeting.setCursor(Qt.PointingHandCursor)
        self._btn_new_meeting.clicked.connect(self._on_new_meeting)
        top_section.addWidget(self._btn_new_meeting)

        layout.addLayout(top_section)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        active_card = self._create_active_card()
        cards_row.addWidget(active_card, 1)

        stats_card = self._create_stats_card()
        cards_row.addWidget(stats_card, 1)

        layout.addLayout(cards_row)

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

        self._active_meeting_info = QLabel("暂无进行中的站会")
        self._active_meeting_info.setStyleSheet("font-size: 13px; color: #AAAAAA;")
        cl.addWidget(self._active_meeting_info)

        bottom_row = QHBoxLayout()
        self._timer_lbl = QLabel("")
        self._timer_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A90D9;")
        bottom_row.addWidget(self._timer_lbl)

        bottom_row.addStretch()

        self._enter_btn = QPushButton("进入站会 →")
        self._enter_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #3A7BC8;
            }
        """)
        self._enter_btn.setCursor(Qt.PointingHandCursor)
        self._enter_btn.clicked.connect(self._on_enter_meeting)
        self._enter_btn.setEnabled(False)
        bottom_row.addWidget(self._enter_btn)

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

        self._stats_grid = QHBoxLayout()
        self._stats_grid.setSpacing(20)

        self._stat_items = []
        for i in range(4):
            item_widget = QWidget()
            iv = QVBoxLayout(item_widget)
            iv.setContentsMargins(0, 0, 0, 0)
            iv.setSpacing(2)

            val_lbl = QLabel("0")
            val_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A90D9;")
            val_lbl.setAlignment(Qt.AlignCenter)
            iv.addWidget(val_lbl)

            lbl = QLabel("")
            lbl.setStyleSheet("font-size: 11px; color: #888888;")
            lbl.setAlignment(Qt.AlignCenter)
            iv.addWidget(lbl)

            self._stat_items.append((val_lbl, lbl))
            self._stats_grid.addWidget(item_widget)

        cl.addLayout(self._stats_grid)
        return card

    def _setup_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "Sprint", "标题", "出勤率", "状态", "操作"])
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

    def _load_meetings(self):
        self.table.setRowCount(0)
        self.table.setRowCount(1)
        self.table.setItem(0, 0, QTableWidgetItem("加载中..."))
        
        self._loader_thread = MeetingLoaderThread(self.api_client, self._current_team_id)
        self._loader_thread.load_finished.connect(self._on_meetings_loaded)
        self._loader_thread.start()
    
    def _on_meetings_loaded(self, meetings):
        self._meetings = meetings
        self.table.setRowCount(len(meetings))
        for row_idx, meeting in enumerate(meetings):
            self.table.setItem(row_idx, 0, QTableWidgetItem(meeting.get("date", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(meeting.get("sprint", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(meeting.get("title", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(meeting.get("attendance", "")))

            status = meeting.get("status", "")
            status_item = QTableWidgetItem(self._get_status_text(status))
            status_item.setForeground(QBrush(QColor(self._get_status_color(status))))
            self.table.setItem(row_idx, 4, status_item)

            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(4)

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
            view_btn.clicked.connect(lambda checked, mid=meeting["id"]: self._on_view_meeting(mid))

            if status == "created":
                start_btn = QPushButton("开始")
                start_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #52C41A;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 4px;
                        padding: 3px 12px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #43A017;
                    }
                """)
                start_btn.setCursor(Qt.PointingHandCursor)
                start_btn.clicked.connect(lambda checked, mid=meeting["id"]: self._on_start_meeting(mid))
                btn_layout.addWidget(start_btn)

            btn_layout.addWidget(view_btn)

            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)
            self.table.setCellWidget(row_idx, 5, btn_widget)

        active_meeting = next((m for m in meetings if m.get("status") == "active"), None)
        if active_meeting:
            self._active_meeting_info.setText(f"{active_meeting.get('title', '')} · {active_meeting.get('sprint', '')}")
            self._timer_lbl.setText("⏱ 进行中")
            self._enter_btn.setEnabled(True)
            self._enter_btn.clicked.disconnect()
            self._enter_btn.clicked.connect(lambda: self.meeting_enter.emit(active_meeting["id"]))
        else:
            self._active_meeting_info.setText("暂无进行中的站会")
            self._timer_lbl.setText("")
            self._enter_btn.setEnabled(False)

    def _get_status_text(self, status):
        status_map = {
            "created": "待开始",
            "active": "进行中",
            "ended": "已结束"
        }
        return status_map.get(status, status)

    def _get_status_color(self, status):
        color_map = {
            "created": "#F5A623",
            "active": "#52C41A",
            "ended": "#8E8E9E"
        }
        return color_map.get(status, "#8E8E9E")

    def _update_stats(self):
        try:
            summary = self.api_client.get_dashboard_summary(self._current_team_id) if self.api_client else self._get_stub_summary()
        except Exception as e:
            print(f"Failed to load summary: {e}")
            summary = self._get_stub_summary()

        labels = ["本月站会", "出勤率", "完成率", "阻碍"]
        values = [
            f"{summary.get('meeting_count', 0)}次",
            f"{int(summary.get('avg_attendance', 0) * 100)}%",
            f"{int(summary.get('completion_rate', 0) * 100)}%",
            f"{summary.get('active_blockers', 0)}个"
        ]

        for (val_lbl, lbl), label, value in zip(self._stat_items, labels, values):
            val_lbl.setText(value)
            lbl.setText(label)

    def _get_stub_meetings(self):
        return [
            {"id": "1", "date": "2024-06-28", "sprint": "Sprint#12", "title": "每日站会", "status": "ended", "attendance": "4/5"},
            {"id": "2", "date": "2024-06-27", "sprint": "Sprint#12", "title": "每日站会", "status": "ended", "attendance": "5/5"},
            {"id": "3", "date": "2024-06-26", "sprint": "Sprint#12", "title": "每日站会", "status": "ended", "attendance": "4/5"},
            {"id": "4", "date": "2024-06-25", "sprint": "Sprint#11", "title": "每日站会", "status": "ended", "attendance": "5/5"},
            {"id": "5", "date": "2024-06-24", "sprint": "Sprint#11", "title": "每日站会", "status": "ended", "attendance": "4/5"},
        ]

    def _get_stub_summary(self):
        return {"meeting_count": 12, "avg_attendance": 0.87, "completion_rate": 0.73, "active_blockers": 3}

    def _on_new_meeting(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("新建站会")
        dialog.setFixedSize(400, 420)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1A1A2E;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 13px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("站会标题:"))
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("例如：每日站会")
        layout.addWidget(title_edit)

        layout.addWidget(QLabel("日期:"))
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat("yyyy-MM-dd")
        date_edit.setStyleSheet("""
            QDateEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 13px;
            }
        """)
        layout.addWidget(date_edit)

        layout.addWidget(QLabel("Sprint编号:"))
        sprint_edit = QLineEdit()
        sprint_edit.setPlaceholderText("例如：Sprint#12")
        layout.addWidget(sprint_edit)

        layout.addWidget(QLabel("会议模式:"))
        mode_combo = QComboBox()
        mode_combo.addItems(["实时站会", "异步站会"])
        mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 4px;
                color: #E0E0E0;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCI+PHBhdGggZmlsbD0iIzRDNTU2NSIgZD0iTTcgMTBsNSA1IDUtNXoiLz48cGF0aCBmaWxsPSIjOEY5MEFFIiBkPSJNMTcgMTBsLTUgNS01LTV6Ii8+PC9zdmc+);
                width: 16px;
                height: 16px;
            }
        """)
        layout.addWidget(mode_combo)

        layout.addWidget(QLabel("参会成员:"))
        member_list = QListWidget()
        member_list.setStyleSheet("""
            QListWidget {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                color: #E0E0E0;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #0F3460;
            }
        """)
        
        try:
            members = self.api_client.get_team_members(self._current_team_id) if self.api_client else []
        except Exception:
            members = []
        
        if not members:
            members = [
                {"id": "1", "name": "张三"},
                {"id": "2", "name": "李四"},
                {"id": "3", "name": "王五"},
                {"id": "4", "name": "赵六"},
            ]
        
        for member in members:
            item = QListWidgetItem(member["name"])
            item.setData(Qt.UserRole, member["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            member_list.addItem(item)
        layout.addWidget(member_list)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.close)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #8E8E9E;
                border: 1px solid #2A2A4A;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("创建")
        create_btn.clicked.connect(lambda: self._create_meeting(dialog, title_edit.text(), date_edit.date().toString("yyyy-MM-dd"), sprint_edit.text(), mode_combo.currentIndex(), member_list))
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5BA0E9;
            }
        """)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def _create_meeting(self, dialog, title, meeting_date, sprint_no, mode_index, member_list):
        if not title.strip():
            QMessageBox.warning(self, "警告", "请输入站会标题")
            return

        selected_ids = []
        for i in range(member_list.count()):
            item = member_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_ids.append(item.data(Qt.UserRole))

        if not selected_ids:
            QMessageBox.warning(self, "警告", "请至少选择一位参会成员")
            return

        form_type = "realtime" if mode_index == 0 else "async"

        if self.api_client:
            try:
                result = self.api_client.create_meeting(
                    team_id=self._current_team_id,
                    title=title,
                    meeting_date=meeting_date,
                    participant_ids=selected_ids,
                    sprint_no=sprint_no,
                    form_type=form_type
                )
                if result.get("success") or result.get("id"):
                    QMessageBox.information(self, "成功", "站会创建成功")
                    dialog.close()
                    self._load_meetings()
                    self._update_stats()
                    if isinstance(result, dict) and (result.get("meeting") or result.get("id")):
                        self.meeting_created.emit(result.get("meeting") or result)
                else:
                    QMessageBox.warning(self, "失败", result.get("error", "创建失败"))
            except Exception as e:
                QMessageBox.warning(self, "失败", f"创建站会失败: {str(e)}")
        else:
            new_meeting = {
                "id": f"meeting_{len(self._meetings) + 1}",
                "title": title,
                "date": meeting_date,
                "sprint": sprint_no or "-",
                "attendance_rate": "0/0",
                "status": "pending",
                "participant_ids": selected_ids,
                "form_type": form_type
            }
            self._meetings.append(new_meeting)
            QMessageBox.information(self, "成功", "站会创建成功（模拟）")
            dialog.close()
            self.activate()

    def _on_start_meeting(self, meeting_id):
        if self.api_client:
            try:
                result = self.api_client.start_meeting(meeting_id)
                if result.get("success"):
                    QMessageBox.information(self, "成功", "站会已开始")
                    self.activate()
                else:
                    QMessageBox.warning(self, "失败", result.get("error", "启动失败"))
            except Exception as e:
                QMessageBox.warning(self, "失败", f"启动站会失败: {str(e)}")
        else:
            for m in self._meetings:
                if m["id"] == meeting_id:
                    m["status"] = "active"
            QMessageBox.information(self, "成功", "站会已开始（模拟）")
            self.activate()

    def _on_view_meeting(self, meeting_id):
        self.view_meeting.emit(meeting_id)

    def _on_enter_meeting(self):
        active_meeting = next((m for m in self._meetings if m.get("status") == "active"), None)
        if active_meeting:
            self.meeting_enter.emit(active_meeting["id"])
