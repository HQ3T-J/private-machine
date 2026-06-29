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
    "pending": "待处理",
    "in_progress": "进行中",
    "completed": "已完成",
}


class TodoView(QWidget):
    """待办管理页面 — 可独立实例化。"""

    title = "待办管理"

    # 信号
    status_changed = Signal(str, str)  # todo_id, new_status

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._current_status = None  # None = 全部
        self._todos = []
        self._current_row = -1
        self._setup_ui()
        self._apply_style()

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

        self._tabs = {}
        tab_items = [
            ("all", "全部", 12),
            ("pending", "待处理", 4),
            ("in_progress", "进行中", 3),
            ("completed", "已完成", 5),
        ]
        for key, label, count in tab_items:
            btn = QPushButton(f"{label} ({count})")
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
            ("source", "来源"),
            ("assignee", "责任人"),
            ("due", "截止日期"),
            ("status", "状态"),
        ]
        for key, label_text in field_configs:
            row = QHBoxLayout()
            lbl = QLabel(f"{label_text}：")
            lbl.setFixedWidth(70)
            lbl.setStyleSheet("color: #8E8E9E; font-size: 13px;")
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

        btn_layout.addWidget(self._btn_complete)
        btn_layout.addWidget(self._btn_progress)
        btn_layout.addWidget(self._btn_transfer)

        panel_layout.addLayout(btn_layout)
        self._update_detail_panel_buttons(False)

    def _update_detail_panel_buttons(self, enabled: bool):
        self._btn_complete.setEnabled(enabled)
        self._btn_progress.setEnabled(enabled)
        self._btn_transfer.setEnabled(enabled)

    # ── 数据加载 ──
    def activate(self):
        """页面激活时刷新数据。"""
        if self.api_client:
            self._todos = self.api_client.get_todos(self._current_status)
        else:
            self._todos = self._get_stub_todos(self._current_status)
        self._populate_table()

    def _get_stub_todos(self, status):
        """独立实例化时的占位数据。"""
        data = [
            {"id": "1", "content": "修复登录页面 Bug", "priority": "high", "status": "pending",
             "assignee": "张三", "due": "明天", "source": "06-25 站会"},
            {"id": "2", "content": "重构用户模块接口", "priority": "medium", "status": "in_progress",
             "assignee": "李四", "due": "本周五", "source": "06-24 站会"},
            {"id": "3", "content": "编写单元测试", "priority": "low", "status": "completed",
             "assignee": "王五", "due": "已完成", "source": "06-23 站会"},
            {"id": "4", "content": "更新 API 文档", "priority": "medium", "status": "pending",
             "assignee": "赵六", "due": "下周一", "source": "06-25 站会"},
            {"id": "5", "content": "性能优化 - 首页加载", "priority": "high", "status": "in_progress",
             "assignee": "张三", "due": "今天", "source": "06-25 站会"},
        ]
        if status:
            data = [t for t in data if t["status"] == status]
        return data

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
            due_item = QTableWidgetItem(todo["due"])
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
            self._detail_title.setText(todo["content"])
            self._detail_fields["priority"].setText(todo["priority"])
            pip = self._detail_fields["priority"]
            pc = PRIORITY_COLORS.get(todo["priority"], "#8E8E9E")
            pip.setStyleSheet(f"color: {pc}; font-size: 13px; font-weight: bold;")
            self._detail_fields["source"].setText(todo.get("source", "—"))
            self._detail_fields["assignee"].setText(todo.get("assignee", "—"))
            self._detail_fields["due"].setText(todo.get("due", "—"))
            st = STATUS_LABELS.get(todo["status"], todo["status"])
            self._detail_fields["status"].setText(st)
            self._update_detail_panel_buttons(True)

    # ── 状态变更 ──
    def _mark_status(self, new_status: str):
        if self._current_row < 0 or self._current_row >= len(self._todos):
            return
        tid = self._todos[self._current_row]["id"]
        self._todos[self._current_row]["status"] = new_status
        self._populate_table()
        self.status_changed.emit(tid, new_status)

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
        for t in self._todos:
            if t["id"] == tid:
                t["status"] = status
                break
        self._populate_table()

    def _delete_todo(self, row):
        if 0 <= row < len(self._todos):
            del self._todos[row]
            self._populate_table()

    # ── 样式 ──
    def _apply_style(self):
        self.setStyleSheet("""
            #todoTabBar {
                background-color: #16213E;
                border-bottom: 1px solid #2A2A4A;
            }
            #todoTabBar QPushButton {
                background: transparent;
                color: #8E8E9E;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            #todoTabBar QPushButton:hover {
                background-color: #1A1A3E;
                color: #E0E0E0;
            }
            #todoTabBar QPushButton:checked {
                background-color: #0F3460;
                color: #4A9ED9;
                font-weight: bold;
            }
            #todoSeparator {
                background-color: #2A2A4A;
                max-height: 1px;
            }
            QTableWidget {
                background-color: #1A1A2E;
                alternate-background-color: #1E1E36;
                color: #E0E0E0;
                border: none;
                gridline-color: #2A2A4A;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid #2A2A4A;
            }
            QTableWidget::item:selected {
                background-color: #0F3460;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #16213E;
                color: #8E8E9E;
                padding: 8px 6px;
                border: none;
                border-bottom: 1px solid #2A2A4A;
                font-size: 12px;
                font-weight: bold;
            }
            #todoDetailPanel {
                background-color: #16213E;
                border-left: 1px solid #2A2A4A;
            }
            #detailTitle {
                color: #E0E0E0;
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
            #btnMarkComplete:disabled {
                background-color: #3A3A5A;
                color: #6E6E8E;
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
            #btnMarkProgress:disabled {
                background-color: #3A3A5A;
                color: #6E6E8E;
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
            #btnTransfer:disabled {
                background-color: #3A3A5A;
                color: #6E6E8E;
            }
            QMenu {
                background-color: #1A1A2E;
                color: #E0E0E0;
                border: 1px solid #2A2A4A;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
            }
            QMenu::item:selected {
                background-color: #0F3460;
            }
        """)
