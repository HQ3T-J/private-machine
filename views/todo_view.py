# views/todo_view.py — 待办管理页面
"""待办管理视图：左侧表格 + 右侧详情面板，支持 Tab 筛选、右键操作与批量操作。"""

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
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont, QAction
from views.todo_detail_view import TodoDetailDialog
from views.ai_todo_view import SummaryTodoDialog


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
    """待办管理页面 — 支持多选批量操作和右键菜单。"""

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
        self._tab_keys = ["all", "pending", "in_progress", "reviewing", "completed"]
        self._tab_labels = {"all": "全部", "pending": "待处理", "in_progress": "进行中", "reviewing": "审核中", "completed": "已完成"}
        for key in self._tab_keys:
            btn = QPushButton(self._tab_labels[key])
            btn.setCheckable(True)
            btn.setObjectName(f"tab_{key}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_tab_clicked(k))
            self._tabs[key] = btn
            tab_layout.addWidget(btn)

        tab_layout.addStretch()
        # 纪要转待办按钮
        summary_btn = QPushButton("📋 纪要转待办")
        summary_btn.setFixedHeight(30)
        summary_btn.setCursor(Qt.PointingHandCursor)
        summary_btn.setStyleSheet("QPushButton{color:#4A9ED9;border:1px solid #4A9ED9;border-radius:4px;padding:2px 10px;font-size:11px;background:transparent;} QPushButton:hover{background:rgba(74,158,217,0.2);}")
        summary_btn.clicked.connect(self._on_summary_to_todo)
        tab_layout.addWidget(summary_btn)
        layout.addWidget(tab_bar)

        # ── 批量操作栏（多选时出现）──
        self._batch_bar = QFrame()
        self._batch_bar.setObjectName("batchBar")
        self._batch_bar.setFixedHeight(40)
        self._batch_bar.setVisible(False)
        self._batch_bar.setStyleSheet("#batchBar{background-color:#16213E;border-bottom:1px solid #2A2A4A;}")
        batch_layout = QHBoxLayout(self._batch_bar)
        batch_layout.setContentsMargins(12, 4, 12, 4)
        batch_layout.setSpacing(8)
        self._batch_label = QLabel("已选 0 项")
        self._batch_label.setStyleSheet("font-size:12px;color:#4A90D9;")
        batch_layout.addWidget(self._batch_label)
        batch_layout.addStretch()
        batch_complete = QPushButton("全部完成")
        batch_complete.setCursor(Qt.PointingHandCursor)
        batch_complete.setStyleSheet("QPushButton{color:#52C41A;border:1px solid #52C41A;border-radius:3px;padding:3px 10px;font-size:11px;background:transparent;} QPushButton:hover{background:#52C41A;color:#FFF;}")
        batch_complete.clicked.connect(lambda: self._batch_mark_status("completed"))
        batch_layout.addWidget(batch_complete)
        batch_progress = QPushButton("全部进行中")
        batch_progress.setCursor(Qt.PointingHandCursor)
        batch_progress.setStyleSheet("QPushButton{color:#F5A623;border:1px solid #F5A623;border-radius:3px;padding:3px 10px;font-size:11px;background:transparent;} QPushButton:hover{background:#F5A623;color:#FFF;}")
        batch_progress.clicked.connect(lambda: self._batch_mark_status("in_progress"))
        batch_layout.addWidget(batch_progress)
        batch_delete = QPushButton("批量删除")
        batch_delete.setCursor(Qt.PointingHandCursor)
        batch_delete.setStyleSheet("QPushButton{color:#E74C3C;border:1px solid #E74C3C;border-radius:3px;padding:3px 10px;font-size:11px;background:transparent;} QPushButton:hover{background:#E74C3C;color:#FFF;}")
        batch_delete.clicked.connect(self._batch_delete)
        batch_layout.addWidget(batch_delete)
        layout.addWidget(self._batch_bar)

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
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.itemSelectionChanged.connect(self._on_multi_selection_changed)

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

        self._detail_title = QLabel("选择一条待办")
        self._detail_title.setObjectName("detailTitle")
        self._detail_title.setWordWrap(True)
        self._detail_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        panel_layout.addWidget(self._detail_title)

        panel_layout.addSpacing(8)

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
        counts = {"all": len(self._todos), "pending": 0, "in_progress": 0, "reviewing": 0, "completed": 0}
        for t in self._todos:
            s = t.get("status", "")
            s = {"PENDING":"pending","IN_PROGRESS":"in_progress","REVIEWING":"reviewing","DONE":"completed","CANCELLED":"completed"}.get(s, s.lower())
            if s in counts: counts[s] += 1
        for key in self._tab_keys:
            if key in self._tabs:
                self._tabs[key].setText(f"{self._tab_labels[key]} ({counts.get(key, 0)})")

    # ── 表格填充 ──
    def _populate_table(self):
        self._table.setRowCount(len(self._todos))
        for row, todo in enumerate(self._todos):
            prio_item = QTableWidgetItem(todo["priority"])
            prio_item.setTextAlignment(Qt.AlignCenter)
            color = PRIORITY_COLORS.get(todo["priority"], "#8E8E9E")
            prio_item.setForeground(QBrush(QColor(color)))
            font = prio_item.font()
            font.setBold(True)
            prio_item.setFont(font)
            self._table.setItem(row, 0, prio_item)
            content_item = QTableWidgetItem(todo["content"])
            self._table.setItem(row, 1, content_item)
            status_label = STATUS_LABELS.get(todo["status"], todo["status"])
            status_item = QTableWidgetItem(status_label)
            status_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, status_item)
            due_str = str(todo.get("dueDate") or todo.get("due", "—"))
            due_item = QTableWidgetItem(due_str[:10] if due_str != "—" else "—")
            due_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, due_item)

    # ── Tab 切换 ──
    def _on_tab_clicked(self, key: str):
        self._current_status = None if key == "all" else key
        for k, btn in self._tabs.items():
            btn.setChecked(k == key)
        self.activate()

    # ── 多选批量操作 ──
    def _on_multi_selection_changed(self):
        """多选时显示/隐藏批量操作栏"""
        rows = self._table.selectionModel().selectedRows()
        count = len(rows)
        self._batch_label.setText(f"已选 {count} 项")
        self._batch_bar.setVisible(count > 1)

    def _get_selected_rows(self) -> list:
        """获取所有选中行的 index（降序，用于安全删除）"""
        indexes = self._table.selectionModel().selectedRows()
        return sorted(set(idx.row() for idx in indexes), reverse=True)

    def _batch_mark_status(self, status: str):
        """批量标记选中项状态"""
        rows = self._get_selected_rows()
        if not rows:
            return
        for row in rows:
            if 0 <= row < len(self._todos):
                tid = self._todos[row].get("id")
                if self.api_client and tid:
                    self.api_client.update_action_item_status(str(tid), status)
                self._todos[row]["status"] = status
        self._populate_table()
        self._update_tab_counts()
        self._batch_bar.setVisible(False)

    def _batch_delete(self):
        """批量删除选中项"""
        rows = self._get_selected_rows()
        if not rows:
            return
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除选中的 {len(rows)} 条待办吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        for row in rows:
            if 0 <= row < len(self._todos):
                tid = self._todos[row].get("id")
                if self.api_client and tid:
                    self.api_client.delete_todo(str(tid))
                del self._todos[row]
        self._populate_table()
        self._update_tab_counts()
        self._batch_bar.setVisible(False)

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
            ct = todo.get("completedAt")
            label = self._detail_fields.get("completedAt")
            if label and ct:
                label.setText(f"完成于 {str(ct)[:16]}")
                label.setVisible(True)
            elif label:
                label.setVisible(False)
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
        menu.addAction("✎ 编辑")
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

    def _on_summary_to_todo(self):
        """打开纪要转待办对话框"""
        teams = self.api_client.get_teams() if self.api_client else []
        if teams:
            team_id = teams[0].get('id')
            dlg = SummaryTodoDialog(self.api_client, team_id, self)
            if dlg.exec() == 1:
                self._load_todos()

    def _show_detail(self, row):
        """打开待办详情弹窗"""
        if 0 <= row < len(self._todos):
            dlg = TodoDetailDialog(self._todos[row], self.api_client, None, self)
            if dlg.exec() == 1:
                self._load_todos()
