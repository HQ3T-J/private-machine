# views/todo_view.py — 待办管理页面
"""待办管理视图：左侧表格 + 右侧详情面板，支持 Tab 筛选与右键操作。"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QSplitter,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont, QAction


# ── 优先级颜色映射 ──
PRIORITY_COLORS = {
    "high": "#E74C3C",    # 红色
    "medium": "#F5A623",  # 橙色
    "low": "#52C41A",     # 绿色
}

STATUS_LABELS = {
    "pending": "待处理", "PENDING": "待处理",
    "in_progress": "进行中", "IN_PROGRESS": "进行中",
    "completed": "已完成", "DONE": "已完成",
    "cancelled": "已取消", "CANCELLED": "已取消",
}


class TodoView(QWidget):
    """待办管理页面 — 可独立实例化。"""

    title = "待办管理"

    # 信号
    status_changed = Signal(str, str)  # todo_id, new_status

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "待办管理"
        self._todos: list = []
        self._current_status = None
        self._current_row = -1
        self._is_team_view = False
        self._setup_ui()

    # ── UI 构建 ──
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部 Tab 栏 ──
        tab_bar = QFrame()
        tab_bar.setObjectName("todoTabBar")
        tab_bar.setFixedHeight(48)
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(16, 8, 16, 8)
        tab_layout.setSpacing(4)

        # 我的/团队 切换
        self._view_toggle = QPushButton("🔒 我的")
        self._view_toggle.setCheckable(True); self._view_toggle.setChecked(True)
        self._view_toggle.setFixedHeight(30)
        self._view_toggle.setStyleSheet("QPushButton{border:1px solid #555;border-radius:4px;padding:2px 8px;font-size:11px;} QPushButton:checked{border-color:#4A90D9;color:#4A90D9;}")
        self._view_toggle.setCursor(Qt.PointingHandCursor)
        self._view_toggle.clicked.connect(self._on_view_toggle)
        tab_layout.addWidget(self._view_toggle)
        tab_layout.addSpacing(12)

        self._tabs = {}
        self._tab_keys = ["all", "pending", "in_progress", "completed"]
        self._tab_labels = {"all": "全部", "pending": "待处理", "in_progress": "进行中", "completed": "已完成"}
        for key in self._tab_keys:
            btn = QPushButton(self._tab_labels[key])
            btn.setCheckable(True)
            btn.setObjectName(f"tab_{key}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_tab_clicked(k))
            self._tabs[key] = btn
            tab_layout.addWidget(btn)

        tab_layout.addStretch()
        layout.addWidget(tab_bar)

        # ── 分割线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("todoSeparator")
        layout.addWidget(sep)

        # ── 主体区域 (QSplitter) ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # 左侧表格（70%）
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["优先级", "内容", "状态", "截止日期"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        # 列宽
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 60)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self._table.setColumnWidth(2, 70)
        self._table.setColumnWidth(3, 80)

        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        # 右侧详情面板（30%）
        self._detail_panel = QFrame()
        self._detail_panel.setObjectName("todoDetailPanel")
        self._detail_panel.setMinimumWidth(240)
        self._setup_detail_panel()

        splitter.addWidget(self._table)
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

        # 右键菜单锚点
        self._context_menu_todo = None

    def _setup_detail_panel(self):
        """构建右侧详情面板。"""
        panel_layout = QVBoxLayout(self._detail_panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(12)

        # 标题
        self._detail_title = QLabel("选择一条待办")
        self._detail_title.setObjectName("detailTitle")
        self._detail_title.setWordWrap(True)
        self._detail_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        panel_layout.addWidget(self._detail_title)

        panel_layout.addSpacing(8)

        # 详情字段
        self._detail_fields = {}
        field_configs = [
            ("priority", "优先级"),
            ("status", "状态"),
            ("assignee", "责任人"),
            ("due", "截止日期"),
        ]
        for key, label_text in field_configs:
            row = QHBoxLayout()
            lbl = QLabel(f"{label_text}：")
            lbl.setFixedWidth(70)
            lbl.setStyleSheet("font-size: 13px;")
            val = QLabel("—")
            val.setWordWrap(True)
            val.setStyleSheet("font-size: 13px;")
            self._detail_fields[key] = val
            row.addWidget(lbl)
            row.addWidget(val, 1)
            panel_layout.addLayout(row)

        panel_layout.addStretch()

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._btn_complete = QPushButton("标记完成")
        self._btn_complete.setObjectName("btnMarkComplete")
        self._btn_complete.setCursor(Qt.PointingHandCursor)
        self._btn_complete.clicked.connect(lambda: self._mark_status("completed"))

        self._btn_progress = QPushButton("标记进行中")
        self._btn_progress.setObjectName("btnMarkProgress")
        self._btn_progress.setCursor(Qt.PointingHandCursor)
        self._btn_progress.clicked.connect(lambda: self._mark_status("in_progress"))

        self._btn_transfer = QPushButton("转交他人")
        self._btn_transfer.setObjectName("btnTransfer")
        self._btn_transfer.setCursor(Qt.PointingHandCursor)

        self._btn_confirm = QPushButton("✓ 确认待办")
        self._btn_confirm.setObjectName("btnConfirm")
        self._btn_confirm.setCursor(Qt.PointingHandCursor)
        self._btn_confirm.clicked.connect(self._on_toggle_confirm)

        btn_layout.addWidget(self._btn_complete)
        btn_layout.addWidget(self._btn_progress)
        btn_layout.addWidget(self._btn_transfer)

        panel_layout.addLayout(btn_layout)
        panel_layout.addWidget(self._btn_confirm)
        self._update_detail_panel_buttons(False)

    def _update_detail_panel_buttons(self, enabled: bool):
        self._btn_complete.setEnabled(enabled)
        self._btn_progress.setEnabled(enabled)
        self._btn_transfer.setEnabled(enabled)

    # ── 数据加载 ──
    def activate(self):
        """页面激活时刷新数据。"""
        self._load_todos()

    def _load_todos(self):
        if not self.api_client:
            self._todos = []
        elif self._is_team_view:
            teams = self.api_client.get_teams()
            tid = teams[0].get("id") if teams else None
            self._todos = self.api_client.get_team_todos(tid) if tid else []
        else:
            self._todos = self.api_client.get_todos(self._current_status)
        self._populate_table()
        self._update_tab_counts()

    def _on_view_toggle(self):
        self._is_team_view = not self._is_team_view
        self._view_toggle.setText("👥 团队" if self._is_team_view else "🔒 我的")
        self._current_status = None
        self._load_todos()

    def _update_tab_counts(self):
        """根据实际数据更新 Tab 计数"""
        counts = {"all": len(self._todos), "pending": 0, "in_progress": 0, "completed": 0}
        for t in self._todos:
            s = t.get("status", "")
            if s in counts: counts[s] += 1
        for key in self._tab_keys:
            if key in self._tabs:
                self._tabs[key].setText(f"{self._tab_labels[key]} ({counts.get(key, 0)})")

    # ── 表格填充 ──
    def _populate_table(self):
        self._table.setRowCount(len(self._todos))
        for row, todo in enumerate(self._todos):
            # 优先级色条
            prio_item = QTableWidgetItem(todo["priority"])
            prio_item.setTextAlignment(Qt.AlignCenter)
            color = PRIORITY_COLORS.get(todo["priority"], "#8E8E9E")
            prio_item.setForeground(QBrush(QColor(color)))
            font = prio_item.font()
            font.setBold(True)
            prio_item.setFont(font)
            self._table.setItem(row, 0, prio_item)

            # 内容
            content_item = QTableWidgetItem(todo["content"])
            self._table.setItem(row, 1, content_item)

            # 状态
            status_label = STATUS_LABELS.get(todo["status"], todo["status"])
            status_item = QTableWidgetItem(status_label)
            status_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, status_item)

            # 截止日期
            due_str = str(todo.get("dueDate") or todo.get("due", "—"))
            due_item = QTableWidgetItem(due_str[:10] if due_str != "—" else "—")
            due_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, due_item)

    # ── Tab 切换 ──
    def _on_tab_clicked(self, key: str):
        self._current_status = None if key == "all" else key
        # 更新按钮选中状态
        for k, btn in self._tabs.items():
            btn.setChecked(k == key)
        self.activate()

    # ── 选中行 → 详情面板 ──
    def _on_selection_changed(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            self._detail_title.setText("选择一条待办")
            for val in self._detail_fields.values():
                val.setText("—")
            self._update_detail_panel_buttons(False)
            self._current_row = -1
            return

        row = rows[0].row()
        self._current_row = row
        if 0 <= row < len(self._todos):
            todo = self._todos[row]
            self._detail_title.setText(todo.get("content", ""))
            self._detail_fields["priority"].setText(todo.get("priority", ""))
            pip = self._detail_fields["priority"]
            pc = PRIORITY_COLORS.get(todo.get("priority", ""), "#8E8E9E")
            pip.setStyleSheet(f"color: {pc}; font-size: 13px; font-weight: bold;")
            # 责任人：从嵌套 assignee 对象或 assigneeName 字段取
            assignee = todo.get("assignee", {}) or {}
            if isinstance(assignee, dict):
                name = assignee.get("displayName") or assignee.get("username", "—")
            else:
                name = todo.get("assigneeName", str(assignee) if assignee else "—")
            self._detail_fields["assignee"].setText(name)
            due = todo.get("dueDate") or todo.get("due", "—")
            self._detail_fields["due"].setText(str(due)[:10] if due != "—" else "—")
            st = STATUS_LABELS.get(todo.get("status", ""), str(todo.get("status", "")))
            self._detail_fields["status"].setText(st)
            # 完成时间
            ct = todo.get("completedAt")
            label = self._detail_fields.get("completedAt")
            if label and ct:
                label.setText(f"完成于 {str(ct)[:16]}")
                label.setVisible(True)
            elif label:
                label.setVisible(False)
            # 确认按钮
            confirmed = todo.get("confirmed", False)
            self._btn_confirm.setText("✓ 已确认" if confirmed else "⚠ 待确认")
            self._btn_confirm.setStyleSheet(
                f"QPushButton{{border:1px solid {'#238636' if confirmed else '#F5A623'};border-radius:4px;padding:4px 8px;font-size:11px;color:{'#FFF' if confirmed else '#F5A623'};background:{'#238636' if confirmed else 'transparent'};}}"
            )
            self._update_detail_panel_buttons(True)

    def _on_toggle_confirm(self):
        if self._current_row < 0 or self._current_row >= len(self._todos):
            return
        todo = self._todos[self._current_row]
        tid = todo.get("id")
        new_confirmed = not todo.get("confirmed", False)
        if self.api_client:
            self.api_client.update_todo(str(tid), {"confirmed": new_confirmed})
        todo["confirmed"] = new_confirmed
        self._show_detail(self._current_row)

    # ── 状态变更 ──
    def _mark_status(self, new_status: str):
        if self._current_row < 0 or self._current_row >= len(self._todos):
            return
        tid = self._todos[self._current_row]["id"]
        if self.api_client:
            self.api_client.update_todo(str(tid), {"status": new_status})
        self._todos[self._current_row]["status"] = new_status
        self._populate_table()
        self._update_tab_counts()
        self.status_changed.emit(str(tid), new_status)

    # ── 右键菜单 ──
    def _on_context_menu(self, pos):
        idx = self._table.indexAt(pos)
        if not idx.isValid():
            return
        row = idx.row()
        if row < 0 or row >= len(self._todos):
            return
        tid = self._todos[row]["id"]
        menu = QMenu(self)

        act_complete = QAction("✓ 标记完成", menu)
        act_complete.triggered.connect(lambda: self._set_todo_status(tid, "completed"))
        menu.addAction(act_complete)

        act_progress = QAction("⟳ 标记进行中", menu)
        act_progress.triggered.connect(lambda: self._set_todo_status(tid, "in_progress"))
        menu.addAction(act_progress)

        menu.addSeparator()

        act_edit = QAction("✎ 编辑", menu)
        menu.addAction(act_edit)

        act_delete = QAction("✕ 删除", menu)
        act_delete.triggered.connect(lambda: self._delete_todo(row))
        menu.addAction(act_delete)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _set_todo_status(self, tid, status):
        if self.api_client:
            self.api_client.update_todo(str(tid), {"status": status})
        for t in self._todos:
            if str(t.get("id")) == str(tid):
                t["status"] = status
                break
        self._populate_table()
        self._update_tab_counts()

    def _delete_todo(self, row):
        if 0 <= row < len(self._todos):
            tid = self._todos[row].get("id")
            if self.api_client and tid:
                self.api_client.delete_todo(str(tid))
            del self._todos[row]
            self._populate_table()
            self._update_tab_counts()

    # ── 样式 ──
    def _apply_style(self):
        self.setStyleSheet("""
            #todoTabBar {
                border-bottom: 1px solid transparent;
            }
            #todoTabBar QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            #todoTabBar QPushButton:checked {
                color: #4A9ED9;
                font-weight: bold;
            }
            #todoSeparator {
                max-height: 1px;
            }
            QTableWidget {
                border: none;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px 6px;
            }
            QHeaderView::section {
                padding: 8px 6px;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            #todoDetailPanel {
                border-left: 1px solid transparent;
            }
            #btnMarkComplete {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            #btnMarkComplete:hover {
                background-color: #45A818;
            }
            #btnMarkProgress {
                background-color: #F5A623;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            #btnMarkProgress:hover {
                background-color: #D4901E;
            }
            #btnTransfer {
                background-color: #4A9ED9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            #btnTransfer:hover {
                background-color: #3A8EC9;
            }
        """)
