# views/ai_todo_view.py — 纪要转待办
"""站会纪要进一步处理：选择站会 → 自动从AI纪要生成待办"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox,
)
from PySide6.QtCore import Qt
from widgets import EmptyState


class SummaryTodoDialog(QDialog):
    """从站会AI纪要进一步处理（打开专属次级界面）"""

    def __init__(self, api_client=None, team_id=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.team_id = team_id
        self._meetings = []
        self.setWindowTitle("纪要转待办")
        self.setFixedSize(480, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title = QLabel("选择有 AI 纪要的站会")
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(title)

        hint = QLabel("选中站会后，AI 纪要将被进一步处理，阻碍项和计划项会自动转为待办。")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 12px; color: #8E8E9E;")
        layout.addWidget(hint)

        self._list = QListWidget()
        self._list.setStyleSheet("QListWidget{border:1px solid #2A2A4E;border-radius:6px;font-size:13px;} QListWidget::item{padding:8px 12px;}")
        self._list.itemDoubleClicked.connect(self._on_convert)
        layout.addWidget(self._list, 1)

        self._empty = EmptyState("📋", "暂无纪要", "站会完成后执行 AI 分析即可生成纪要")
        self._empty.setVisible(False)
        layout.addWidget(self._empty, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()

        cancel = QPushButton("关闭")
        cancel.setStyleSheet("QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;border-radius:4px;padding:6px 16px;font-size:12px;}")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        bottom.addWidget(cancel)

        self._convert_btn = QPushButton("转为待办")
        self._convert_btn.setStyleSheet("QPushButton{background:#238636;color:#FFF;border:none;border-radius:4px;padding:6px 16px;font-size:12px;font-weight:bold;} QPushButton:hover{background:#2EA043;} QPushButton:disabled{background:#2A2A4E;color:#8E8E9E;}")
        self._convert_btn.setCursor(Qt.PointingHandCursor)
        self._convert_btn.setEnabled(False)
        self._convert_btn.clicked.connect(self._on_convert)
        bottom.addWidget(self._convert_btn)

        layout.addLayout(bottom)

        # Load data
        self._load()

    def _load(self):
        if not self.api_client or not self.team_id:
            return
        # 使用新的端点获取有纪要的站会
        data = self.api_client._get(f"/api/meetings/with-summary?teamId={self.team_id}")
        if isinstance(data, list):
            self._meetings = data
        elif isinstance(data, dict) and "content" in data:
            self._meetings = data["content"]
        else:
            self._meetings = []

        self._refresh()

    def _refresh(self):
        self._list.clear()
        if not self._meetings:
            self._list.setVisible(False)
            self._empty.setVisible(True)
            return
        self._list.setVisible(True)
        self._empty.setVisible(False)
        for m in self._meetings:
            title = m.get("title") or f"Sprint#{m.get('sprintNo','?')}"
            date = str(m.get("createdAt", ""))[:10]
            item = QListWidgetItem(f"{title}  ({date})")
            item.setData(Qt.UserRole, m.get("id"))
            self._list.addItem(item)
        self._list.setCurrentRow(0)
        self._convert_btn.setEnabled(True)

    def _on_convert(self):
        current = self._list.currentItem()
        if not current:
            return
        mid = current.data(Qt.UserRole)
        if not mid or not self.api_client:
            return

        reply = QMessageBox.question(
            self, "确认", "将该站会的 AI 纪要进一步处理，阻碍项和计划项将自动转为待办?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        resp = self.api_client._post(f"/api/action-items/ai-from-summary/{mid}", {})
        if resp and resp.get("code") == 200:
            data = resp.get("data", {})
            QMessageBox.information(self, "完成", data.get("message", "转换完成"))
            self.accept()
        else:
            msg = resp.get("message", "转换失败") if resp else "后端无响应"
            QMessageBox.warning(self, "错误", msg)
