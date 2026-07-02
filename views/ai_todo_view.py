# views/ai_todo_view.py — AI 智能识别待办
"""AI 智能待办生成弹窗：输入文本 → AI 解析 → 批量创建。"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QCheckBox, QScrollArea, QWidget, QMessageBox,
)
from PySide6.QtCore import Qt


class AITodoDialog(QDialog):
    """AI 待办生成对话框。"""

    def __init__(self, api_client=None, team_id=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.team_id = team_id
        self._results = []
        self._checkboxes = []
        self.setWindowTitle("AI 智能识别待办")
        self.setFixedSize(500, 520)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        label = QLabel("输入会议纪要或需求描述:")
        label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(label)

        self._input = QTextEdit()
        self._input.setPlaceholderText(
            "支持任意格式，AI 会自动识别待办项。\n"
            "优先级标记: [高/中/低] 或 ! (高) !! (中) !!! (低)\n"
            "责任人标记: @用户名\n"
            "示例:\n"
            "张三负责修复登录Bug [高]\n"
            "李四完成用户手册第三章"
        )
        self._input.setMinimumHeight(120)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel1 = QPushButton("取消")
        cancel1.setStyleSheet(
            "QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;"
            "border-radius:4px;padding:6px 16px;font-size:12px;}"
        )
        cancel1.setCursor(Qt.PointingHandCursor)
        cancel1.clicked.connect(self.reject)
        btn_row.addWidget(cancel1)

        analyze_btn = QPushButton("智能识别")
        analyze_btn.setStyleSheet(
            "QPushButton{background:#4A9ED9;color:#FFF;border:none;border-radius:4px;"
            "padding:6px 16px;font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#5DB3E8;}"
        )
        analyze_btn.setCursor(Qt.PointingHandCursor)
        analyze_btn.clicked.connect(self._on_analyze)
        btn_row.addWidget(analyze_btn)

        layout.addLayout(btn_row)

        # Results area
        self._results_label = QLabel("")
        self._results_label.setStyleSheet("font-size: 12px; color: #8E8E9E;")
        layout.addWidget(self._results_label)

        self._results_scroll = QScrollArea()
        self._results_scroll.setWidgetResizable(True)
        self._results_container = QWidget()
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setSpacing(4)
        self._results_layout.addStretch()
        self._results_scroll.setWidget(self._results_container)
        layout.addWidget(self._results_scroll, 1)

        # Bottom buttons
        bottom = QHBoxLayout()
        bottom.addStretch()

        cancel2 = QPushButton("取消")
        cancel2.setStyleSheet(
            "QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;"
            "border-radius:4px;padding:6px 16px;font-size:12px;}"
        )
        cancel2.setCursor(Qt.PointingHandCursor)
        cancel2.clicked.connect(self.reject)
        bottom.addWidget(cancel2)

        self._create_btn = QPushButton("批量创建 (0)")
        self._create_btn.setStyleSheet(
            "QPushButton{background:#238636;color:#FFF;border:none;border-radius:4px;"
            "padding:6px 16px;font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#2EA043;}"
            "QPushButton:disabled{background:#2A2A4E;color:#8E8E9E;}"
        )
        self._create_btn.setCursor(Qt.PointingHandCursor)
        self._create_btn.setEnabled(False)
        self._create_btn.clicked.connect(self._on_create)
        bottom.addWidget(self._create_btn)

        layout.addLayout(bottom)

    def _on_analyze(self):
        text = self._input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入内容")
            return
        if not self.api_client or not self.team_id:
            QMessageBox.warning(self, "提示", "未连接到后端")
            return

        resp = self.api_client.ai_generate_todos(text, self.team_id)
        if not resp or resp.get("code") != 200:
            msg = resp.get("message", "解析失败") if resp else "后端无响应"
            QMessageBox.warning(self, "错误", msg)
            return

        data = resp.get("data", {})
        if isinstance(data, list):
            self._results = data
        elif isinstance(data, dict):
            self._results = data.get("todos", [])

        self._show_results()

    def _show_results(self):
        # Clear
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._checkboxes = []

        for i, todo in enumerate(self._results):
            content = todo.get("content", "")
            priority = todo.get("priority", "MEDIUM")
            assignee = todo.get("suggestedAssignee") or todo.get("suggestedAssignee") or "--"

            priority_color = {"HIGH": "#E74C3C", "MEDIUM": "#F5A623", "LOW": "#52C41A"}.get(priority, "#8E8E9E")

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 4, 4, 4)
            row_layout.setSpacing(8)

            cb = QCheckBox()
            cb.setChecked(True)
            self._checkboxes.append(cb)
            row_layout.addWidget(cb)

            prio_lbl = QLabel(priority)
            prio_lbl.setStyleSheet(f"color:{priority_color};font-size:11px;font-weight:bold;")
            prio_lbl.setFixedWidth(50)
            row_layout.addWidget(prio_lbl)

            content_lbl = QLabel(content)
            content_lbl.setWordWrap(True)
            content_lbl.setStyleSheet("font-size:12px;")
            row_layout.addWidget(content_lbl, 1)

            assignee_lbl = QLabel(assignee[:8] if assignee != "--" else "--")
            assignee_lbl.setStyleSheet("font-size:11px;color:#8E8E9E;")
            assignee_lbl.setFixedWidth(60)
            row_layout.addWidget(assignee_lbl)

            self._results_layout.insertWidget(self._results_layout.count() - 1, row)

        checked = sum(1 for cb in self._checkboxes if cb.isChecked())
        self._results_label.setText(f"识别结果 ({len(self._results)} 项)")
        self._create_btn.setText(f"批量创建 ({checked})")
        self._create_btn.setEnabled(checked > 0)

        # Update count on checkbox toggle
        for cb in self._checkboxes:
            cb.toggled.connect(self._update_count)

    def _update_count(self):
        checked = sum(1 for cb in self._checkboxes if cb.isChecked())
        self._create_btn.setText(f"批量创建 ({checked})")
        self._create_btn.setEnabled(checked > 0)

    def _on_create(self):
        if not self.api_client:
            QMessageBox.warning(self, "提示", "未连接到后端")
            return

        created = 0
        failed = 0
        for i, todo in enumerate(self._results):
            if i < len(self._checkboxes) and not self._checkboxes[i].isChecked():
                continue
            content = todo.get("content", "")
            priority = todo.get("priority", "MEDIUM")
            resp = self.api_client.create_todo(
                content=content,
                assignee_id=todo.get("suggestedAssignee"),
                priority=priority,
            )
            # create_todo returns the response dict directly
            if resp and resp.get("code") == 200:
                created += 1
            else:
                failed += 1

        if created > 0:
            QMessageBox.information(self, "完成", f"已创建 {created} 条待办")
            self.accept()
        else:
            QMessageBox.warning(self, "失败", f"创建失败: {failed} 条")
