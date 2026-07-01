# views/dashboard_view.py — 数据看板 V2 完全重制
"""数据看板：统计卡片 + 趋势折线图 + 阻碍分布 + 排行表 + Sprint筛选。
所有数据通过 API 实时获取，无硬编码。"""

import sys, os
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path: sys.path.insert(0, _PROJECT_ROOT)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QProgressBar, QSizePolicy, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QPointF, QTimer
from widgets import EmptyState
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPolygonF
from widgets import StatCard

# ── 辅助样式 ──
def _combo_style(): return "QComboBox{border-radius:4px;padding:4px 8px;font-size:12px;}"
def _table_style(): return "QTableWidget{border:none;font-size:12px;} QTableWidget::item{padding:4px 6px;} QHeaderView::section{padding:6px;border:none;font-weight:bold;font-size:11px;}"

_BLOCKER_MAP = {"技术":"tech","资源":"resource","沟通":"communication","其他":"other"}

# ═══════════════════════════════════════════════════════════
#  UI 组件（StatCard 统一由 widgets 提供）
# ═══════════════════════════════════════════════════════════

class TrendMiniChart(QFrame):
    def __init__(self, title, color="#4A9ED9", parent=None):
        super().__init__(parent)
        self.setObjectName("TrendMiniChart")
        self.setMinimumSize(340,160); self.setFixedHeight(160)
        self._title, self._data, self._color = title, [], QColor(color)
        self.setStyleSheet("#TrendMiniChart{border-radius:8px;}")

    def set_data(self, data): self._data = data; self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QColor("#8E8E9E")); p.setFont(QFont("Segoe UI",10,QFont.Bold))
        p.drawText(12,18,self._title)
        if len(self._data) < 2:
            p.setPen(QColor("#6E6E8E")); p.drawText(self.rect(),Qt.AlignCenter,"暂无足够数据")
            p.end(); return
        ml,mr,mt,mb = 40,20,30,30
        w,h = self.width()-ml-mr, self.height()-mt-mb
        rates = [d["rate"] for d in self._data]
        mn,mx = min(rates), max(rates); rng = mx-mn or 0.1
        tx = lambda i: ml+int(w*i/(len(self._data)-1))
        ty = lambda r: mt+h-int(h*(r-mn)/rng)
        pts = [(tx(i),ty(r)) for i,r in enumerate(rates)]
        fp = pts + [(pts[-1][0],mt+h),(pts[0][0],mt+h)]
        p.setBrush(QBrush(QColor(self._color.red(),self._color.green(),self._color.blue(),40)))
        p.setPen(Qt.NoPen); p.drawPolygon(QPolygonF([QPointF(x,y) for x,y in fp]))
        p.setPen(QPen(self._color,2)); p.setBrush(Qt.NoBrush)
        for i in range(len(pts)-1): p.drawLine(pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1])
        p.setBrush(QBrush(self._color)); p.setPen(Qt.NoPen)
        for x,y in pts: p.drawEllipse(x-3,y-3,6,6)
        p.setPen(QColor("#6E6E8E")); p.setFont(QFont("Segoe UI",7))
        for i,d in enumerate(self._data): p.drawText(tx(i)-14,mt+h+16,28,14,Qt.AlignCenter,d["date"])
        p.end()

class BlockerPieChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BlockerPieChart")
        self.setMinimumSize(300,180); self.setFixedHeight(180)
        self._data = []; self.setStyleSheet("#BlockerPieChart{border-radius:8px;}")

    def set_data(self, data): self._data = data; self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QColor("#8E8E9E")); p.setFont(QFont("Segoe UI",10,QFont.Bold))
        p.drawText(12,18,"阻碍类型分布")
        if not self._data:
            p.setPen(QColor("#6E6E8E")); p.drawText(self.rect(),Qt.AlignCenter,"暂无阻碍数据")
            p.end(); return
        total = sum(d["count"] for d in self._data) or 1
        bw = self.width()-32-60; y=36
        for item in self._data[:4]:
            c = QColor(item.get("color","#888"))
            p.setBrush(QBrush(c)); p.setPen(Qt.NoPen)
            p.drawRoundedRect(16,y,14,14,3,3)
            p.setPen(QColor("#C0C0D0")); p.setFont(QFont("Segoe UI",10))
            p.drawText(36,y+12,f"{item.get('label',item['type'])} ({item['count']})")
            fw = int(bw*item["count"]/total) if total else 0
            p.setBrush(QBrush(c)); p.drawRoundedRect(180,y+1,fw,12,4,4)
            p.setPen(QColor("#8E8E9E")); p.drawText(180+bw+8,y+12,f"{round(item['count']/total*100)}%")
            y+=32
        p.end()

class FilterTag(QFrame):
    remove_clicked = Signal(str)
    def __init__(self, text, tag_key, parent=None):
        super().__init__(parent)
        self.tag_key = tag_key
        self.setObjectName("FilterTag"); self.setFixedHeight(26)
        l = QHBoxLayout(self); l.setContentsMargins(8,2,4,2); l.setSpacing(4)
        lb = QLabel(text); lb.setStyleSheet("font-size:11px;"); l.addWidget(lb)
        cb = QPushButton("x"); cb.setFixedSize(16,16)
        cb.setStyleSheet("QPushButton{color:#8E8E9E;border:none;font-size:12px;} QPushButton:hover{color:#E74C3C;}")
        cb.setCursor(Qt.PointingHandCursor); cb.clicked.connect(lambda: self.remove_clicked.emit(self.tag_key))
        l.addWidget(cb)
        self.setStyleSheet("#FilterTag{border-radius:4px;}")

# ═══════════════════════════════════════════════════════════
#  DashboardView
# ═══════════════════════════════════════════════════════════

class DashboardView(QWidget):
    title = "数据看板"

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._team_id = None
        self._filters = {"sprint": None, "blocker_type": None, "userId": None, "dateFrom": None, "dateTo": None, "sortBy": "completionRate"}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,16,20,16); layout.setSpacing(12)

        # ── 标题栏 ──
        hdr = QHBoxLayout()
        t = QLabel("数据看板"); t.setStyleSheet("font-size:20px;font-weight:bold;")
        hdr.addWidget(t); hdr.addStretch()
        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setStyleSheet("QPushButton{background:transparent;color:#4A90D9;border:1px solid #4A90D9;border-radius:4px;padding:4px 12px;font-size:12px;} QPushButton:hover{background:rgba(74,144,217,0.2);}")
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.activate)
        hdr.addWidget(self._refresh_btn)
        layout.addLayout(hdr)

        # ── 筛选栏 ──
        fb = QHBoxLayout(); fb.setSpacing(10)
        fb.addWidget(QLabel("Sprint：")); fb.itemAt(fb.count()-1).widget().setStyleSheet("font-size:13px;")
        self._sprint_combo = QComboBox(); self._sprint_combo.addItem("全部")
        self._sprint_combo.setFixedWidth(120); self._sprint_combo.setStyleSheet(_combo_style())
        self._sprint_combo.currentTextChanged.connect(self._on_filter_changed)
        fb.addWidget(self._sprint_combo)

        fb.addWidget(QLabel("阻碍：")); fb.itemAt(fb.count()-1).widget().setStyleSheet("font-size:13px;")
        self._blocker_combo = QComboBox()
        self._blocker_combo.addItems(["全部","技术","资源","沟通","其他"])
        self._blocker_combo.setFixedWidth(100); self._blocker_combo.setStyleSheet(_combo_style())
        self._blocker_combo.currentTextChanged.connect(self._on_filter_changed)
        fb.addWidget(self._blocker_combo)

        fb.addWidget(QLabel("成员：")); fb.itemAt(fb.count()-1).widget().setStyleSheet("font-size:13px;")
        self._member_combo = QComboBox(); self._member_combo.addItem("全部")
        self._member_combo.setFixedWidth(120); self._member_combo.setStyleSheet(_combo_style())
        self._member_combo.currentTextChanged.connect(self._on_filter_changed)
        fb.addWidget(self._member_combo)

        fb.addWidget(QLabel("时间：")); fb.itemAt(fb.count()-1).widget().setStyleSheet("font-size:13px;")
        self._time_combo = QComboBox()
        self._time_combo.addItems(["全部","本周","本月","近7天","近30天"])
        self._time_combo.setFixedWidth(100); self._time_combo.setStyleSheet(_combo_style())
        self._time_combo.currentTextChanged.connect(self._on_filter_changed)
        fb.addWidget(self._time_combo)

        self._reset_btn = QPushButton("🔄 重置")
        self._reset_btn.setStyleSheet("QPushButton{background:transparent;color:#E74C3C;border:1px solid #E74C3C;border-radius:4px;padding:4px 10px;font-size:11px;}")
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.clicked.connect(self._on_reset_filters)
        fb.addWidget(self._reset_btn)
        fb.addStretch()
        layout.addLayout(fb)

        # ── 标签行 ──
        self._tags_layout = QHBoxLayout(); self._tags_layout.setSpacing(6); self._tags_layout.addStretch()
        layout.addLayout(self._tags_layout)

        # ── 统计卡片 ──
        sr = QHBoxLayout(); sr.setSpacing(16); self._cards = {}
        for k, t, c in [("meetings","站会次数","#4A9ED9"),("attendance","平均出勤率","#52C41A"),
                         ("completion","待办完成率","#F5A623"),("blockers","活跃阻碍","#E74C3C")]:
            card = StatCard(t, "—", accent_color=c, fixed_size=(200,100)); self._cards[k] = card; sr.addWidget(card)
        sr.addStretch(); layout.addLayout(sr)

        # ── 趋势图 ──
        tr = QHBoxLayout(); tr.setSpacing(16)
        self._trend_att = TrendMiniChart("出勤率趋势","#52C41A")
        self._trend_comp = TrendMiniChart("完成率趋势","#F5A623")
        tr.addWidget(self._trend_att); tr.addWidget(self._trend_comp); tr.addStretch()
        layout.addLayout(tr)

        # ── 底部 ──
        br = QHBoxLayout(); br.setSpacing(16)
        self._blocker = BlockerPieChart(); br.addWidget(self._blocker)

        rf = QFrame(); rf.setObjectName("RankFrame"); rf.setMinimumSize(340,180); rf.setFixedHeight(180)
        rl = QVBoxLayout(rf); rl.setContentsMargins(12,10,12,10)
        rl.addWidget(QLabel("成员完成排行")); rl.itemAt(0).widget().setStyleSheet("font-size:12px;font-weight:bold;")
        self._rank_table = QTableWidget()
        self._rank_table.setColumnCount(5)
        self._rank_table.setHorizontalHeaderLabels(["#","成员","待办","完成率","进度"])
        self._rank_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._rank_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._rank_table.setShowGrid(False); self._rank_table.verticalHeader().setVisible(False)
        self._rank_table.setAlternatingRowColors(True)
        h = self._rank_table.horizontalHeader()
        h.setSectionResizeMode(0,QHeaderView.Fixed); self._rank_table.setColumnWidth(0,30)
        h.setSectionResizeMode(1,QHeaderView.Stretch)
        h.setSectionResizeMode(2,QHeaderView.Fixed); self._rank_table.setColumnWidth(2,50)
        h.setSectionResizeMode(3,QHeaderView.Fixed); self._rank_table.setColumnWidth(3,60)
        h.setSectionResizeMode(4,QHeaderView.Fixed); self._rank_table.setColumnWidth(4,100)
        self._rank_table.setStyleSheet(_table_style())
        rl.addWidget(self._rank_table)
        rf.setStyleSheet("#RankFrame{border-radius:8px;}")
        br.addWidget(rf); layout.addLayout(br)
        layout.addStretch()

    # ── 激活 ──
    def activate(self):
        self._team_id = None
        if self.api_client:
            teams = self.api_client.get_teams()
            if teams:
                self._team_id = teams[0].get("id")
                self._load_sprints()
                self._load_members()
                self._load_all_data()
                return
        self._clear_all()

    def _load_members(self):
        if not self._team_id: return
        self._member_combo.blockSignals(True); self._member_combo.clear(); self._member_combo.addItem("全部")
        team_data = self.api_client._get(f"/api/teams/{self._team_id}")
        if team_data:
            for m in team_data.get("members", []):
                name = m.get("name") or m.get("username") or m.get("user_id", "?")
                self._member_combo.addItem(name, m.get("user_id"))
        self._member_combo.blockSignals(False)

    def _load_sprints(self):
        if not self._team_id: return
        meetings = self.api_client.get_meetings(self._team_id) or []
        sprints = sorted(set(m.get("sprintNo") for m in meetings if m.get("sprintNo") is not None), reverse=True)
        cur = self._sprint_combo.currentText()
        self._sprint_combo.blockSignals(True); self._sprint_combo.clear(); self._sprint_combo.addItem("全部")
        for s in sprints: self._sprint_combo.addItem(f"Sprint #{s}")
        idx = self._sprint_combo.findText(cur)
        self._sprint_combo.setCurrentIndex(idx if idx>=0 else 0)
        self._sprint_combo.blockSignals(False)

    def _load_all_data(self):
        if not self._team_id or not self.api_client: return
        c = self.api_client; f = self._filters
        sprint = f.get("sprint"); sprint_str = str(sprint) if sprint else None

        # Summary — 用后端 dateFrom/dateTo
        s = c.get_dashboard_summary(self._team_id, sprint_str, f.get("dateFrom"), f.get("dateTo")) or {}
        self._cards["meetings"].update_value(str(s.get("totalMeetings",0)))
        ar = s.get("avgAttendanceRate",0)
        self._cards["attendance"].update_value(f"{int(ar*100)}%" if isinstance(ar,float) and ar<=1 else f"{ar}%")
        cr = s.get("completionRate",0)
        self._cards["completion"].update_value(f"{int(cr*100)}%" if isinstance(cr,float) and cr<=1 else f"{cr}%")
        self._cards["blockers"].update_value(str(s.get("activeBlockers",0)))

        # Trends — 用后端 userId
        uid = f.get("userId")
        att_data = c.get_dashboard_trend(self._team_id, "attendance", uid)
        comp_data = c.get_dashboard_trend(self._team_id, "completion", uid)
        self._trend_att.set_data(att_data)
        self._trend_comp.set_data(comp_data)

        # Blocker — 用后端 trend blocker 端点
        bt = _BLOCKER_MAP.get(f.get("blocker_type")) if f.get("blocker_type") else None
        blocker_data = c.get_dashboard_trend(self._team_id, "blocker")
        self._blocker.set_data(blocker_data)

        # Ranking — 用后端 sortBy
        ranking = c.get_member_ranking(self._team_id, f.get("sortBy", "completionRate"))
        self._rank_table.setRowCount(len(ranking))
        for i, m in enumerate(ranking):
            ri = QTableWidgetItem(str(i+1)); ri.setTextAlignment(Qt.AlignCenter)
            self._rank_table.setItem(i,0,ri)
            self._rank_table.setItem(i,1,QTableWidgetItem(m.get("name","?")))
            ti = QTableWidgetItem(str(m.get("total",0))); ti.setTextAlignment(Qt.AlignCenter)
            self._rank_table.setItem(i,2,ti)
            rt = m.get("rate",0)
            if isinstance(rt,float) and rt<=1: rt*=100
            ri2 = QTableWidgetItem(f"{int(rt)}%"); ri2.setTextAlignment(Qt.AlignCenter)
            self._rank_table.setItem(i,3,ri2)
            pb = QProgressBar(); pb.setRange(0,100); pb.setValue(int(rt)); pb.setTextVisible(False)
            pb.setStyleSheet("QProgressBar{border:none;border-radius:4px;height:8px;} QProgressBar::chunk{border-radius:4px;background:#4A9ED9;}")
            self._rank_table.setCellWidget(i,4,pb)

    def _clear_all(self):
        for c in self._cards.values(): c.update_value("—")
        self._trend_att.set_data([]); self._trend_comp.set_data([])
        self._blocker.set_data([]); self._rank_table.setRowCount(0)
        self._sprint_combo.blockSignals(True); self._sprint_combo.clear(); self._sprint_combo.addItem("全部")
        self._sprint_combo.blockSignals(False)

    # ── Sprint 筛选 ──
    def _on_filter_changed(self, _text=None):
        # Sprint
        s = self._sprint_combo.currentText()
        if s == "全部": self._filters["sprint"] = None
        else:
            try: self._filters["sprint"] = int(s.split("#")[1])
            except: self._filters["sprint"] = None
        # Blocker type
        b = self._blocker_combo.currentText()
        self._filters["blocker_type"] = None if b == "全部" else b
        # Member
        self._filters["userId"] = self._member_combo.currentData()  # None=全部
        # Time range
        from datetime import date, timedelta
        today = date.today()
        t = self._time_combo.currentText()
        if t == "本周":
            start = today - timedelta(days=today.weekday())
            self._filters["dateFrom"] = start.isoformat()
            self._filters["dateTo"] = today.isoformat()
        elif t == "本月":
            self._filters["dateFrom"] = today.replace(day=1).isoformat()
            self._filters["dateTo"] = today.isoformat()
        elif t == "近7天":
            self._filters["dateFrom"] = (today - timedelta(days=6)).isoformat()
            self._filters["dateTo"] = today.isoformat()
        elif t == "近30天":
            self._filters["dateFrom"] = (today - timedelta(days=29)).isoformat()
            self._filters["dateTo"] = today.isoformat()
        else:
            self._filters["dateFrom"] = self._filters["dateTo"] = None
        self._load_all_data()
        self._sync_tags()

    def _on_reset_filters(self):
        self._sprint_combo.setCurrentIndex(0)
        self._blocker_combo.setCurrentIndex(0)
        self._member_combo.setCurrentIndex(0)
        self._time_combo.setCurrentIndex(0)

    def _sync_tags(self): pass  # 简化：按需实现标签行


# ═══════════════════════════════════════════════════════════
#  数据辅助函数（模块级）
# ═══════════════════════════════════════════════════════════

def _item_in_sprint(item, meetings, sprint_no):
    """判断待办是否属于指定 sprint 的站会"""
    mid = item.get("meeting", {}).get("id") if isinstance(item.get("meeting"), dict) else item.get("meetingId")
    if mid is None: return False
    for m in meetings:
        if m.get("id") == mid and m.get("sprintNo") == sprint_no:
            return True
    return False

def _build_trend_from_meetings(meetings, trend_type, items=None):
    """从站会列表构建趋势数据"""
    if not meetings: return []
    sorted_m = sorted(meetings, key=lambda m: m.get("createdAt", ""))
    result = []
    for m in sorted_m[-10:]:  # 最近10次
        date = m.get("createdAt", "")[:10]
        if trend_type == "attendance":
            # 从 meeting 的 participants 计算
            participants = m.get("participants", [])
            if participants:
                spoken = sum(1 for p in participants if p.get("has_spoken"))
                rate = spoken / len(participants) if participants else 0
            else:
                rate = 0
        else:  # completion
            if items:
                mid = m.get("id")
                mitems = [i for i in items if _item_meeting_id(i) == mid]
                done = sum(1 for i in mitems if i.get("status") in ("DONE", "completed"))
                rate = done / len(mitems) if mitems else 0
            else:
                rate = 0
        result.append({"date": date[-5:], "rate": rate})
    return result

def _item_meeting_id(item):
    m = item.get("meeting")
    if isinstance(m, dict): return m.get("id")
    return item.get("meetingId")

def _build_blocker_dist(meetings, api_client):
    """从站会发言中统计阻碍分布"""
    if not meetings: return []
    cats = {"tech": 0, "resource": 0, "communication": 0, "other": 0}
    labels = {"tech": "技术问题", "resource": "资源问题", "communication": "沟通问题", "other": "其他"}
    colors = {"tech": "#1890FF", "resource": "#F5A623", "communication": "#7B7B7B", "other": "#D0D0D0"}
    for m in meetings:
        try:
            speeches = api_client.get_speeches(str(m.get("id"))) or []
            for s in speeches:
                b = (s.get("blockers") or "").lower()
                if not b: continue
                if any(kw in b for kw in ["技术","bug","代码","环境","数据库","服务器","compile","error"]): cats["tech"] += 1
                elif any(kw in b for kw in ["资源","人力","排期","人手","budget","equipment"]): cats["resource"] += 1
                elif any(kw in b for kw in ["沟通","需求","确认","对齐","不清楚","等待"]): cats["communication"] += 1
                else: cats["other"] += 1
        except Exception:
            pass  # 单个站会的发言获取失败不影响整体统计
    return [{"type": k, "label": labels[k], "count": cats[k], "color": colors[k]} for k in cats if cats[k] > 0]

def _build_ranking(items, api_client):
    """从待办列表计算成员排行"""
    if not items: return []
    by_user = {}
    for i in items:
        assignee = i.get("assignee", {}) or {}
        uid = assignee.get("id") or i.get("assigneeId") or "unknown"
        name = assignee.get("displayName") or assignee.get("username") or uid
        if uid not in by_user: by_user[uid] = {"name": name, "total": 0, "done": 0}
        by_user[uid]["total"] += 1
        if i.get("status") in ("DONE", "completed"): by_user[uid]["done"] += 1
    ranking = []
    for uid, data in by_user.items():
        rate = data["done"] / data["total"] if data["total"] else 0
        ranking.append({"name": data["name"], "total": data["total"], "rate": rate})
    ranking.sort(key=lambda x: x["rate"], reverse=True)
    return ranking
