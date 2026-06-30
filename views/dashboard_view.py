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
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPolygonF

# ── 辅助样式 ──
def _combo_style(): return "QComboBox{border-radius:4px;padding:4px 8px;font-size:12px;}"
def _table_style(): return "QTableWidget{border:none;font-size:12px;} QTableWidget::item{padding:4px 6px;} QHeaderView::section{padding:6px;border:none;font-weight:bold;font-size:11px;}"

_BLOCKER_MAP = {"技术":"tech","资源":"resource","沟通":"communication","其他":"other"}

# ═══════════════════════════════════════════════════════════
#  UI 组件
# ═══════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, title, value="—", subtitle="", color="#4A9ED9", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFixedSize(200, 100)
        l = QVBoxLayout(self); l.setContentsMargins(16,12,16,12); l.setSpacing(2)
        t = QLabel(title); t.setStyleSheet("font-size:12px;"); l.addWidget(t)
        vr = QHBoxLayout(); vr.setSpacing(6)
        self._val = QLabel(str(value))
        self._val.setStyleSheet(f"color:{color};font-size:28px;font-weight:bold;")
        vr.addWidget(self._val); vr.addStretch(); l.addLayout(vr)
        if subtitle:
            s = QLabel(subtitle); s.setStyleSheet("font-size:11px;"); l.addWidget(s)
        l.addStretch()
        self.setStyleSheet(f"#StatCard{{border-radius:8px;border-left:3px solid {color};}}")

    def update_value(self, text): self._val.setText(str(text))

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
        self._filters = {"sprint": None, "blocker_type": None}
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

        # ── Sprint 筛选 ──
        fb = QHBoxLayout(); fb.setSpacing(10)
        fb.addWidget(QLabel("Sprint：")); fb.itemAt(fb.count()-1).widget().setStyleSheet("font-size:13px;")
        self._sprint_combo = QComboBox(); self._sprint_combo.addItem("全部")
        self._sprint_combo.setFixedWidth(140); self._sprint_combo.setStyleSheet(_combo_style())
        self._sprint_combo.currentTextChanged.connect(self._on_sprint_changed)
        fb.addWidget(self._sprint_combo); fb.addStretch()
        layout.addLayout(fb)

        # ── 标签行 ──
        self._tags_layout = QHBoxLayout(); self._tags_layout.setSpacing(6); self._tags_layout.addStretch()
        layout.addLayout(self._tags_layout)

        # ── 统计卡片 ──
        sr = QHBoxLayout(); sr.setSpacing(16); self._cards = {}
        for k, t, c in [("meetings","站会次数","#4A9ED9"),("attendance","平均出勤率","#52C41A"),
                         ("completion","待办完成率","#F5A623"),("blockers","活跃阻碍","#E74C3C")]:
            card = StatCard(t, "—", "", c); self._cards[k] = card; sr.addWidget(card)
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
                self._load_all_data()
                return
        self._clear_all()

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
        c = self.api_client

        # Summary
        s = c.get_dashboard_summary(self._team_id) or {}
        self._cards["meetings"].update_value(str(s.get("totalMeetings",0)))
        ar = s.get("avgAttendanceRate",0)
        self._cards["attendance"].update_value(f"{int(ar*100)}%" if isinstance(ar,float) and ar<=1 else f"{ar}%")
        cr = s.get("completionRate",0)
        self._cards["completion"].update_value(f"{int(cr*100)}%" if isinstance(cr,float) and cr<=1 else f"{cr}%")
        self._cards["blockers"].update_value(str(s.get("activeBlockers",0)))

        # Trends
        at = c.get_dashboard_trend(self._team_id,"attendance") or []
        ct = c.get_dashboard_trend(self._team_id,"completion") or []
        self._trend_att.set_data([{"date":p.get("date","")[-5:],"rate":p.get("rate",0) if isinstance(p.get("rate"),(int,float)) else p.get("attended",0)/max(p.get("total",1),1)} for p in at] if at else [])
        self._trend_comp.set_data([{"date":p.get("date","")[-5:],"rate":p.get("rate",0) if isinstance(p.get("rate"),(int,float)) else 0} for p in ct] if ct else [])

        # Blocker distribution
        bd = c.get_dashboard_trend(self._team_id,"blocker") or []
        self._blocker.set_data(bd if bd else [])

        # Ranking
        rk = c.get_member_ranking(self._team_id) or []
        self._rank_table.setRowCount(len(rk))
        medals = {0:"1",1:"2",2:"3"}
        for i,m in enumerate(rk):
            ri = QTableWidgetItem(medals.get(i,str(i+1))); ri.setTextAlignment(Qt.AlignCenter)
            self._rank_table.setItem(i,0,ri)
            nm = m.get("username") or m.get("userId","?")
            self._rank_table.setItem(i,1,QTableWidgetItem(nm))
            ti = QTableWidgetItem(str(m.get("totalItems",0))); ti.setTextAlignment(Qt.AlignCenter)
            self._rank_table.setItem(i,2,ti)
            rt = m.get("completionRate",0)
            if isinstance(rt,float) and rt<=1: rt*=100
            ri2 = QTableWidgetItem(f"{int(rt)}%"); ri2.setTextAlignment(Qt.AlignCenter)
            self._rank_table.setItem(i,3,ri2)
            pb = QProgressBar(); pb.setRange(0,100); pb.setValue(int(rt)); pb.setTextVisible(False)
            pb.setStyleSheet("QProgressBar{border:none;border-radius:4px;background:#2A2A4A;height:8px;} QProgressBar::chunk{border-radius:4px;background:#4A9ED9;}")
            self._rank_table.setCellWidget(i,4,pb)

    def _clear_all(self):
        for c in self._cards.values(): c.update_value("—")
        self._trend_att.set_data([]); self._trend_comp.set_data([])
        self._blocker.set_data([]); self._rank_table.setRowCount(0)
        self._sprint_combo.blockSignals(True); self._sprint_combo.clear(); self._sprint_combo.addItem("全部")
        self._sprint_combo.blockSignals(False)

    # ── Sprint 筛选 ──
    def _on_sprint_changed(self, text):
        if text == "全部": self._filters["sprint"] = None
        else:
            try: self._filters["sprint"] = int(text.split("#")[1])
            except: self._filters["sprint"] = None
        self._load_all_data()

    def _sync_tags(self): pass  # 简化：按需实现标签行
