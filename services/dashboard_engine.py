# services/dashboard_engine.py — 桥接层：通过 API 客户端获取数据
"""桥接模块：将旧调用重定向到 HTTP API 客户端"""

from api_client import APIClient


def _client():
    return APIClient()


def compute_summary(meetings=None, action_items=None, api_client=None, team_id=None) -> dict:
    c = api_client or _client()
    if team_id is None:
        teams = c.get_teams()
        team_id = teams[0].get("id") if teams else None
    if team_id is None:
        return {}
    result = c.get_dashboard_summary(team_id) or {}
    return {
        "total_meetings": result.get("totalMeetings", 0),
        "avg_attendance_rate": result.get("avgAttendanceRate", 0),
        "completion_rate": result.get("completionRate", 0),
        "active_blockers": result.get("activeBlockers", 0),
        "total_action_items": result.get("totalActionItems", 0),
        "completed_items": result.get("completedItems", 0),
    }


def compute_attendance_trend(meetings=None, limit=10) -> list:
    c = _client()
    teams = c.get_teams()
    if not teams:
        return []
    team_id = teams[0].get("id")
    return c.get_dashboard_trend(team_id, "attendance") or []


def compute_completion_trend(meetings=None, action_items=None, limit=10) -> list:
    c = _client()
    teams = c.get_teams()
    if not teams:
        return []
    team_id = teams[0].get("id")
    return c.get_dashboard_trend(team_id, "completion") or []


def compute_blocker_distribution(meetings=None) -> list:
    c = _client()
    teams = c.get_teams()
    if not teams:
        return []
    team_id = teams[0].get("id")
    return c.get_dashboard_trend(team_id, "blocker") or []


def compute_member_ranking(action_items=None) -> list:
    c = _client()
    teams = c.get_teams()
    if not teams:
        return []
    team_id = teams[0].get("id")
    return c.get_member_ranking(team_id) or []


class FilterConfig:
    def __init__(self):
        self.sprint_no = None
        self.blocker_type = None
        self.user_id = None
        self.date_from = None
        self.date_to = None


def apply_filters(data, filters):
    return data
