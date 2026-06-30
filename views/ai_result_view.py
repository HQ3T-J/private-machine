# views/ai_result_view.py — AI 纪要结果页，接入 AI 引擎
"""AI 纪要结果页（2×2 网格 + 底部操作栏）。

activate(speeches_text: str) 触发 AI 引擎 run_pipeline()，
LLM 不可用时使用本地解析降级。
展示结构化结果：昨日完成/今日计划/阻碍汇总(带类型标签)/Action Item(带优先级色标)。
"""

import sys
import os
import re

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QSizePolicy, QProgressBar,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor

from services.ai_engine import run_pipeline, parse_chat_log, AIConfig


# ── 优先级 & 阻碍色标 ──
_PRIORITY_STYLE = {
    "high": ("#FF4D4D", "🔴"),
    "medium": ("#FFB84D", "🟡"),
    "low": ("#4DCC4D", "🟢"),
}
_BLOCKER_COLORS = {
    "tech": "#FF6B6B", "resource": "#FFB84D",
    "communication": "#4A90D9", "other": "#8E8E9E",
}
_BLOCKER_LABELS = {
    "tech": "技术", "resource": "资源", "communication": "沟通", "other": "其他",
}

class AIResultView(QWidget):
    """AI 纪要结果页。

    Signals:
        finished: 纪要生成完成
        request_regenerate: 用户点击重新生成
    """

    finished = Signal(dict)
    request_regenerate = Signal()

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "AI 纪要"
        self._result_data = None
        self._speeches_text = ""
        self._ai_config = None
        self._setup_ui()

    # _base_style 已移除——所有颜色由全局主题控制
    # QGroupBox 保留圆角和内边距

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("🤖 AI 站会纪要")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        # 加载指示器
        self._loading_bar = QProgressBar()
        self._loading_bar.setRange(0, 0)
        self._loading_bar.setFixedHeight(4)
        self._loading_bar.setTextVisible(False)
        self._loading_bar.setStyleSheet(
            "QProgressBar{border:none;}QProgressBar::chunk{background:#4A90D9;}"
        )
        self._loading_bar.hide()
        layout.addWidget(self._loading_bar)

        self._loading_label = QLabel("AI 整理中...")
        self._loading_label.setAlignment(Qt.AlignCenter)
        self._loading_label.setStyleSheet("color: #4A90D9; font-size: 14px; padding: 8px;")
        self._loading_label.hide()
        layout.addWidget(self._loading_label)

        # 2×2 网格
        grid = QVBoxLayout()
        grid.setSpacing(14)

        row1 = QHBoxLayout()
        row1.setSpacing(14)
        self._yesterday_group = self._create_list_group("✅ 昨日完成")
        row1.addWidget(self._yesterday_group, 1)
        self._today_group = self._create_list_group("📋 今日计划")
        row1.addWidget(self._today_group, 1)
        grid.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(14)
        self._blockers_group = self._create_blockers_group()
        row2.addWidget(self._blockers_group, 1)
        self._actions_group = self._create_actions_group()
        row2.addWidget(self._actions_group, 1)
        grid.addLayout(row2)

        layout.addLayout(grid, 1)

        # 底部按钮栏
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        self._regen_btn = QPushButton("重新生成")
        self._regen_btn.setStyleSheet(_btn_style("transparent", "transparent", outline=True))
        self._regen_btn.setCursor(Qt.PointingHandCursor)
        self._regen_btn.clicked.connect(self._on_regenerate)
        bottom_bar.addWidget(self._regen_btn)

        bottom_bar.addStretch()

        self._confirm_btn = QPushButton("确认并结束站会")
        self._confirm_btn.setStyleSheet(_btn_style("#4A90D9", "#5BA0E9", bold=True))
        self._confirm_btn.setCursor(Qt.PointingHandCursor)
        self._confirm_btn.clicked.connect(lambda: self.finished.emit(self._result_data or {}))
        bottom_bar.addWidget(self._confirm_btn)

        self._share_btn = QPushButton("分享")
        self._share_btn.setStyleSheet(_btn_style("transparent", "transparent", outline=True))
        self._share_btn.setCursor(Qt.PointingHandCursor)
        bottom_bar.addWidget(self._share_btn)

        layout.addLayout(bottom_bar)

    # ── 激活 ──
    def activate(self, speeches=None, ai_config: AIConfig = None):
        """激活页面：接收发言文本，调用 AI 引擎。"""
        self._speeches_text = speeches or ""
        self._ai_config = ai_config

        self._show_loading(True)
        QTimer.singleShot(300, self._run_pipeline)

    def _run_pipeline(self):
        """执行 AI 流水线并刷新 UI。LLM 不可用时降级为本地解析。"""
        result = self._try_ai_pipeline()
        if result is None:
            result = self._local_fallback(self._speeches_text)

        self._result_data = result
        self._refresh_display(result)
        self._show_loading(False)
        self.finished.emit(result)

    def _try_ai_pipeline(self):
        """尝试调用 LLM 流水线，失败返回 None。"""
        if not self._ai_config or not self._ai_config.api_key:
            return None
        try:
            pipeline_result = run_pipeline(self._speeches_text, self._ai_config)
            structured = pipeline_result.get("step2_structured", [])
            summary = pipeline_result.get("step3_summary", {})
            action_items = summary.get("action_items", [])
            if summary.get("error"):
                return None  # LLM 调用失败 → 降级
        except Exception:
            return None

        return self._convert_pipeline_result(structured, summary)

    def _convert_pipeline_result(self, structured: list, summary: dict) -> dict:
        """将 run_pipeline 返回的结构转换为视图所需格式。"""
        yesterday_list = [f"{s.get('speaker', '')}：{s.get('yesterday', '')}"
                          for s in structured if s.get("yesterday")]
        today_list = [f"{s.get('speaker', '')}：{s.get('today', '')}"
                      for s in structured if s.get("today")]

        blockers = []
        for s in structured:
            for b in s.get("blockers", []):
                b_type = b.get("type", "other")
                blockers.append({
                    "member": s.get("speaker", ""),
                    "content": b.get("desc", ""),
                    "type": b_type,
                })

        action_items = summary.get("action_items", [])
        return {
            "yesterday_list": yesterday_list,
            "today_list": today_list,
            "blockers": blockers,
            "action_items": action_items,
            "summary": summary.get("summary", ""),
        }

    def _local_fallback(self, text: str) -> dict:
        """本地降级：用 parse_chat_log + 正则提取结构化信息。"""
        parsed = parse_chat_log(text)
        yesterday_list = []
        today_list = []
        blockers = []
        action_items = []

        for item in parsed:
            speaker = item["speaker"]
            content = item["content"]

            # 提取昨日/今日/阻碍
            y, t, bl, bs = _extract_speech_parts(content)
            if y:
                yesterday_list.append(f"{speaker}：{y}")
            if t:
                today_list.append(f"{speaker}：{t}")
            if bl == "阻碍" and bs:
                b_type = _infer_blocker_type(bs)
                blockers.append({"member": speaker, "content": bs, "type": b_type})

            # 从今日计划推断 Action Item
            if t and any(kw in t for kw in ["完成", "开发", "部署", "编写", "梳理", "优化", "重构"]):
                priority = "high" if any(w in t for w in ["紧急", "本周五"]) else "medium"
                action_items.append({
                    "content": f"{speaker}：{t}",
                    "priority": priority,
                    "assignee": speaker,
                })

        return {
            "yesterday_list": yesterday_list,
            "today_list": today_list,
            "blockers": blockers,
            "action_items": action_items,
            "summary": "",
        }

    def _show_loading(self, visible: bool):
        self._loading_bar.setVisible(visible)
        self._loading_label.setVisible(visible)
        self._regen_btn.setEnabled(not visible)
        self._confirm_btn.setEnabled(not visible)

    def _on_regenerate(self):
        self.request_regenerate.emit()
        self.activate(self._speeches_text, self._ai_config)

    # ── 刷新显示 ──
    def _refresh_display(self, data: dict):
        self._fill_list(self._yesterday_group.findChild(QListWidget),
                        data.get("yesterday_list", []))
        self._fill_list(self._today_group.findChild(QListWidget),
                        data.get("today_list", []))

        # 阻碍汇总（带类型标签）
        lst_bl = self._blockers_group.findChild(QListWidget)
        lst_bl.clear()
        for b in data.get("blockers", []):
            b_type = b.get("type", "other")
            b_label = _BLOCKER_LABELS.get(b_type, "其他")
            color = _BLOCKER_COLORS.get(b_type, "#8E8E9E")
            item = QListWidgetItem(f"[{b_label}] {b['member']}：{b['content']}")
            item.setForeground(QColor(color))
            lst_bl.addItem(item)

        # Action Items（带优先级色标）
        lst_act = self._actions_group.findChild(QListWidget)
        lst_act.clear()
        for a in data.get("action_items", []):
            priority = a.get("priority", "medium")
            color, emoji = _PRIORITY_STYLE.get(priority, _PRIORITY_STYLE["medium"])
            text = f"{emoji} {a.get('content', '')}  — {a.get('assignee', '')}"
            item = QListWidgetItem(text)
            item.setForeground(QColor(color))
            lst_act.addItem(item)

    # ── 工厂方法 ──
    def _create_list_group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        gl = QVBoxLayout(group)
        gl.setContentsMargins(10, 14, 10, 10)
        lst = QListWidget()
        lst.setStyleSheet(_list_style())
        gl.addWidget(lst)
        return group

    def _create_blockers_group(self) -> QGroupBox:
        group = QGroupBox("🚧 阻碍汇总")
        gl = QVBoxLayout(group)
        gl.setContentsMargins(10, 14, 10, 10)
        lst = QListWidget()
        lst.setStyleSheet(_list_style(blocker=True))
        gl.addWidget(lst)
        return group

    def _create_actions_group(self) -> QGroupBox:
        group = QGroupBox("📌 Action Item")
        gl = QVBoxLayout(group)
        gl.setContentsMargins(10, 14, 10, 10)
        lst = QListWidget()
        lst.setStyleSheet(_list_style())
        gl.addWidget(lst)
        return group

    @staticmethod
    def _fill_list(lst: QListWidget, items: list):
        lst.clear()
        for text in items:
            lst.addItem(text)


# ── 本地解析辅助 ──

def _extract_speech_parts(content: str):
    """从发言内容中提取：yesterday, today, 阻碍。"""
    yesterday = ""
    today = ""
    blocker_key = ""
    blocker_desc = ""

    # 匹配 "昨天xxx今天xxx" 或 "昨天：xxx今天：xxx"
    m = re.search(r'昨天[：:]?\s*(.+?)(?:今天|今日|。|$)', content)
    if m:
        yesterday = m.group(1).strip().rstrip("，。")
    m = re.search(r'(?:今天|今日)[：:]?\s*(.+?)(?:阻碍|阻塞|遇到|。|$)', content)
    if m:
        today = m.group(1).strip().rstrip("，。")

    # 阻碍匹配：阻碍：xxx 或 遇到一个阻碍：xxx
    m = re.search(r'(阻碍|阻塞)[：:]\s*(.+?)(?:。|，|$)', content)
    if m:
        blocker_key = "阻碍"
        blocker_desc = m.group(2).strip()
    if not blocker_desc:
        m = re.search(r'(遇到.*?阻碍[：:]?\s*(.+?))(?:。|，|$)', content)
        if m:
            blocker_key = "阻碍"
            blocker_desc = m.group(2).strip() if m.lastindex >= 2 else m.group(1)

    # 过滤"无"类阻碍
    if blocker_desc and any(w in blocker_desc for w in ["无", "没有", "没"]):
        blocker_desc = ""

    return yesterday, today, blocker_key, blocker_desc


def _infer_blocker_type(desc: str) -> str:
    """推断阻碍类型。"""
    d = desc.lower()
    if any(kw in d for kw in ["环境", "服务器", "机器", "测试环境", "预发", "宕机", "staging"]):
        return "resource"
    if any(kw in d for kw in ["技术", "bug", "编译", "构建", "打包", "性能", "超时", "代码", "数据库"]):
        return "tech"
    if any(kw in d for kw in ["需求", "确认", "沟通", "产品", "不明确", "不清楚", "评审"]):
        return "communication"
    return "other"


# ── 样式辅助 ──

def _btn_style(bg: str, hover: str, bold: bool = False, outline: bool = False) -> str:
    fw = "font-weight: bold;" if bold else ""
    border_style = "border: 1px solid #4A90D9;" if outline else "border: none;"
    text_color = "#4A90D9" if outline else "#FFFFFF"
    return f"""
        QPushButton {{
            background-color: {bg}; color: {text_color};
            {border_style} border-radius: 6px;
            padding: 8px 20px; font-size: 13px; {fw}
        }}
        QPushButton:hover {{ background-color: {hover}; }}
    """


def _list_style(blocker: bool = False) -> str:
    bg = "" if blocker else "transparent"
    return f"""
        QListWidget {{
            background-color: transparent; border: none;
            font-size: 13px;
        }}
        QListWidget::item {{
            padding: 6px 4px; border-bottom: 1px solid transparent;
            background-color: {bg}; border-radius: 4px; margin: 2px 0;
        }}
    """
