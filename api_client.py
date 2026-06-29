# api_client.py — API 客户端桩（单例模式）
# 所有方法返回空占位数据，不做真实网络请求

from typing import Optional


class APIClient:
    """单例 API 客户端，提供所有占位数据。"""

    _instance: Optional["APIClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.token = None
        return cls._instance

    # ── 认证 ──
    def login(self, username: str, password: str) -> dict:
        return {
            "token": "stub-token-abc123",
            "user": {
                "id": "1",
                "display_name": username,
                "role": "tech_lead",
            },
        }

    # ── 团队 ──
    def get_teams(self) -> list[dict]:
        return [
            {"id": "1", "name": "核心开发组", "role": "tech_lead"},
            {"id": "2", "name": "前端团队", "role": "scrum_master"},
        ]

    def get_team_members(self, team_id: str) -> list[dict]:
        return [
            {"id": "1", "name": "张三", "role": "Tech Lead", "attendance": 0.95, "completion": 0.92},
            {"id": "2", "name": "李四", "role": "Scrum Master", "attendance": 0.88, "completion": 0.75},
            {"id": "3", "name": "王五", "role": "Developer", "attendance": 0.90, "completion": 0.60},
            {"id": "4", "name": "赵六", "role": "Developer", "attendance": 0.72, "completion": 0.45},
            {"id": "5", "name": "孙七", "role": "Observer", "attendance": 0.50, "completion": 0.30},
        ]

    # ── 站会 ──
    def get_meetings(self, team_id: str) -> list[dict]:
        return [
            {
                "id": "1",
                "date": "06-25",
                "sprint": "Sprint #12",
                "attendance": "4/5",
                "completion": "80%",
                "blockers": 2,
            },
            {
                "id": "2",
                "date": "06-26",
                "sprint": "Sprint #12",
                "attendance": "5/5",
                "completion": "85%",
                "blockers": 1,
            },
        ]

    # ── 待办 ──
    def get_todos(self, status: Optional[str] = None) -> list[dict]:
        data = [
            {
                "id": "1",
                "content": "修复登录页面 Bug",
                "priority": "high",
                "status": "pending",
                "assignee": "张三",
                "due": "明天",
                "source": "06-25 站会",
            },
            {
                "id": "2",
                "content": "重构用户模块接口",
                "priority": "medium",
                "status": "in_progress",
                "assignee": "李四",
                "due": "本周五",
                "source": "06-24 站会",
            },
            {
                "id": "3",
                "content": "编写单元测试",
                "priority": "low",
                "status": "completed",
                "assignee": "王五",
                "due": "已完成",
                "source": "06-23 站会",
            },
            {
                "id": "4",
                "content": "更新 API 文档",
                "priority": "medium",
                "status": "pending",
                "assignee": "赵六",
                "due": "下周一",
                "source": "06-25 站会",
            },
            {
                "id": "5",
                "content": "性能优化 - 首页加载",
                "priority": "high",
                "status": "in_progress",
                "assignee": "张三",
                "due": "今天",
                "source": "06-25 站会",
            },
            {
                "id": "6",
                "content": "代码审查 PR#42",
                "priority": "medium",
                "status": "pending",
                "assignee": "李四",
                "due": "明天",
                "source": "06-25 同步",
            },
            {
                "id": "7",
                "content": "修复 SQL 注入漏洞",
                "priority": "high",
                "status": "pending",
                "assignee": "王五",
                "due": "紧急",
                "source": "安全扫描",
            },
            {
                "id": "8",
                "content": "国际化文案整理",
                "priority": "low",
                "status": "in_progress",
                "assignee": "赵六",
                "due": "下周",
                "source": "06-24 站会",
            },
            {
                "id": "9",
                "content": "上线前回归测试",
                "priority": "high",
                "status": "completed",
                "assignee": "张三",
                "due": "已完成",
                "source": "06-25 站会",
            },
            {
                "id": "10",
                "content": "设计评审准备",
                "priority": "medium",
                "status": "completed",
                "assignee": "李四",
                "due": "已完成",
                "source": "06-25 站会",
            },
            {
                "id": "11",
                "content": "CI/CD 流水线修复",
                "priority": "high",
                "status": "completed",
                "assignee": "王五",
                "due": "已完成",
                "source": "06-23 站会",
            },
            {
                "id": "12",
                "content": "依赖版本升级",
                "priority": "low",
                "status": "completed",
                "assignee": "赵六",
                "due": "已完成",
                "source": "06-25 站会",
            },
        ]
        if status:
            data = [t for t in data if t["status"] == status]
        return data

    def update_todo_status(self, todo_id: str, status: str) -> dict:
        return {"id": todo_id, "status": status, "updated": True}

    # ── 看板/仪表盘 ──
    def get_dashboard_summary(self, team_id: str) -> dict:
        return {
            "total_meetings": 12,
            "avg_attendance": 0.87,
            "completion_rate": 0.73,
            "active_blockers": 3,
        }

    def get_dashboard_trend(self, team_id: str) -> list[dict]:
        return [
            {"date": "06-01", "rate": 0.80},
            {"date": "06-03", "rate": 0.85},
            {"date": "06-05", "rate": 0.90},
            {"date": "06-07", "rate": 0.82},
            {"date": "06-09", "rate": 0.88},
            {"date": "06-11", "rate": 0.91},
            {"date": "06-13", "rate": 0.87},
        ]

    def get_member_ranking(self, team_id: str) -> list[dict]:
        return [
            {"name": "张三", "total": 12, "rate": 0.92},
            {"name": "李四", "total": 8, "rate": 0.75},
            {"name": "王五", "total": 15, "rate": 0.60},
            {"name": "赵六", "total": 5, "rate": 0.45},
            {"name": "孙七", "total": 3, "rate": 0.30},
        ]

    # ── 邀请 ──
    def get_invite_code(self, team_id: str) -> str:
        return "A3F8K2"

    def dissolve_team(self, team_id: str) -> dict:
        return {"dissolved": True}
