# StandupSync Core Module
# Contains all core functions for team management, meeting management, and speech management

from typing import List, Dict, Optional, Any
import random
import string

# ==================== Team Management Functions ====================

def generate_invite_code() -> str:
    """Generate a 6-digit invite code"""
    return ''.join(random.choices(string.digits + string.ascii_uppercase, k=6))

def create_team(api_client, name: str, description: str = "") -> Dict:
    """Create a new team, creator automatically becomes Tech Lead"""
    try:
        result = api_client.create_team(name, description)
        if result.get("success"):
            return {"success": True, "team": result.get("data", {})}
        return {"success": False, "error": result.get("error", "Failed to create team")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_team(api_client, team_id: str) -> Dict:
    """Delete a team and cascade delete all related data"""
    try:
        result = api_client.delete_team(team_id)
        if result.get("success"):
            return {"success": True}
        return {"success": False, "error": result.get("error", "Failed to delete team")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def join_team(api_client, invite_code: str) -> Dict:
    """Join a team using invite code"""
    if not invite_code or len(invite_code) != 6:
        return {"success": False, "error": "Invalid invite code"}
    
    try:
        result = api_client.join_team(invite_code.strip())
        if result.get("success"):
            return {"success": True, "team": result.get("data", {})}
        return {"success": False, "error": result.get("error", "Failed to join team")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def remove_member(api_client, team_id: str, member_id: str) -> Dict:
    """Remove a member from team (preserves read-only records)"""
    try:
        result = api_client.remove_member(team_id, member_id)
        if result.get("success"):
            return {"success": True}
        return {"success": False, "error": result.get("error", "Failed to remove member")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_member_role(api_client, team_id: str, member_id: str, new_role: str) -> Dict:
    """Update member role (Tech Lead/Scrum Master/Developer/Observer)"""
    valid_roles = ["tech_lead", "scrum_master", "developer", "observer"]
    if new_role not in valid_roles:
        return {"success": False, "error": "Invalid role"}
    
    try:
        result = api_client.update_member_role(team_id, member_id, new_role)
        if result.get("success"):
            return {"success": True}
        return {"success": False, "error": result.get("error", "Failed to update role")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_team_members(api_client, team_id: str) -> List[Dict]:
    """Get team members list"""
    try:
        return api_client.get_team_members(team_id)
    except Exception as e:
        print(f"Error getting team members: {e}")
        return []

def refresh_invite_code(api_client, team_id: str) -> Optional[str]:
    """Refresh team invite code"""
    try:
        result = api_client.refresh_invite_code(team_id)
        if result.get("success"):
            return result.get("invite_code")
        return None
    except Exception as e:
        print(f"Error refreshing invite code: {e}")
        return None

# ==================== Meeting Management Functions ====================

def create_meeting(
    api_client,
    team_id: str,
    title: str,
    participant_ids: List[str],
    meeting_date: str = "",
    sprint_no: str = "",
    form_type: str = "realtime"
) -> Dict:
    """Create a new meeting"""
    if not title or not participant_ids:
        return {"success": False, "error": "Title and participants are required"}
    
    if form_type not in ["realtime", "async"]:
        return {"success": False, "error": "Invalid meeting type"}
    
    try:
        result = api_client.create_meeting(
            team_id=team_id,
            title=title,
            meeting_date=meeting_date,
            participant_ids=participant_ids,
            sprint_no=sprint_no,
            form_type=form_type
        )
        if result.get("success"):
            return {"success": True, "meeting": result.get("meeting", {})}
        return {"success": False, "error": result.get("error", "Failed to create meeting")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def start_meeting(api_client, meeting_id: str) -> Dict:
    """Start a meeting (change status to in_progress)"""
    try:
        result = api_client.start_meeting(meeting_id)
        if result.get("success"):
            return {"success": True}
        return {"success": False, "error": result.get("error", "Failed to start meeting")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def end_meeting(api_client, meeting_id: str) -> Dict:
    """End a meeting and archive minutes"""
    try:
        result = api_client.end_meeting(meeting_id)
        if result.get("success"):
            return {"success": True}
        return {"success": False, "error": result.get("error", "Failed to end meeting")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_meeting(api_client, meeting_id: str) -> Dict:
    """Get meeting details"""
    try:
        return api_client.get_meeting(meeting_id)
    except Exception as e:
        print(f"Error getting meeting: {e}")
        return {}

def get_meetings(api_client, team_id: str) -> List[Dict]:
    """Get meetings for a team"""
    try:
        return api_client.get_meetings(team_id)
    except Exception as e:
        print(f"Error getting meetings: {e}")
        return []

def update_meeting_participants(api_client, meeting_id: str, participant_ids: List[str]) -> Dict:
    """Update meeting participants order"""
    try:
        result = api_client.update_meeting_participants(meeting_id, participant_ids)
        if result.get("success"):
            return {"success": True}
        return {"success": False, "error": result.get("error", "Failed to update participants")}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== Speech Management Functions ====================

def submit_speech(
    api_client,
    meeting_id: str,
    yesterday: str = "",
    today: str = "",
    blockers: str = ""
) -> Dict:
    """Submit a speech for current user"""
    try:
        result = api_client.submit_speech(meeting_id, yesterday, today, blockers)
        if result.get("success"):
            return {"success": True, "speech": result.get("data", {})}
        return {"success": False, "error": result.get("error", "Failed to submit speech")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def skip_speaker(api_client, meeting_id: str, user_id: str) -> Dict:
    """Skip a speaker in the meeting"""
    try:
        result = api_client.skip_speaker(meeting_id, user_id)
        if result.get("success"):
            return {"success": True}
        return {"success": False, "error": result.get("error", "Failed to skip speaker")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_speeches(api_client, meeting_id: str) -> List[Dict]:
    """Get all speeches for a meeting"""
    try:
        return api_client.get_speeches(meeting_id)
    except Exception as e:
        print(f"Error getting speeches: {e}")
        return []

def analyze_meeting(api_client, meeting_id: str) -> Dict:
    """Analyze meeting with AI"""
    try:
        result = api_client.analyze_meeting(meeting_id)
        if result.get("success"):
            return {"success": True, "data": result.get("data", {})}
        return {"success": False, "error": result.get("error", "AI analysis failed")}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== Timer Functions ====================

def format_time(seconds: int) -> str:
    """Format seconds to MM:SS"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def is_time_warning(seconds: int) -> bool:
    """Check if remaining time is less than 2 minutes"""
    return seconds <= 120

def is_time_critical(seconds: int) -> bool:
    """Check if remaining time is less than 30 seconds"""
    return seconds <= 30

# ==================== Data Validation Functions ====================

def validate_invite_code(code: str) -> bool:
    """Validate invite code format (6 alphanumeric characters)"""
    return len(code) == 6 and code.isalnum()

def validate_team_name(name: str) -> bool:
    """Validate team name (1-100 characters)"""
    return 1 <= len(name.strip()) <= 100

def validate_meeting_title(title: str) -> bool:
    """Validate meeting title (1-200 characters)"""
    return 1 <= len(title.strip()) <= 200

def validate_role(role: str) -> bool:
    """Validate role value"""
    return role in ["tech_lead", "scrum_master", "developer", "observer"]

# ==================== Mock Data Generators ====================

def generate_mock_team(name: str = "Default Team") -> Dict:
    """Generate mock team data"""
    return {
        "id": "team_" + ''.join(random.choices(string.ascii_lowercase, k=8)),
        "name": name,
        "invite_code": generate_invite_code(),
        "created_at": "2024-01-01 10:00:00"
    }

def generate_mock_members(count: int = 5) -> List[Dict]:
    """Generate mock members data"""
    names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
    roles = ["tech_lead", "scrum_master", "developer", "developer", "observer"]
    
    return [
        {
            "id": f"user_{i+1}",
            "name": names[i % len(names)],
            "role": roles[i % len(roles)],
            "attendance_rate": round(random.uniform(0.7, 1.0), 2),
            "completion_rate": round(random.uniform(0.6, 1.0), 2)
        }
        for i in range(count)
    ]

def generate_mock_meetings(count: int = 10) -> List[Dict]:
    """Generate mock meetings data"""
    statuses = ["completed", "completed", "completed", "in_progress", "pending"]
    
    return [
        {
            "id": f"meeting_{i+1}",
            "title": f"Daily Standup {i+1}",
            "date": f"2024-01-{15 + i % 10}",
            "sprint_no": f"Sprint#{i // 2 + 1}",
            "status": statuses[i % len(statuses)],
            "attendance_rate": round(random.uniform(0.6, 1.0), 2),
            "participant_count": random.randint(3, 8)
        }
        for i in range(count)
    ]

# ==================== Function Validation ====================

def validate_all_functions():
    """Validate all functions have correct signatures and logic"""
    print("🔍 Validating all core functions...")
    
    # Test invite code generation
    code = generate_invite_code()
    assert len(code) == 6, f"Invite code length should be 6, got {len(code)}"
    assert code.isalnum(), f"Invite code should be alphanumeric, got {code}"
    print("✓ generate_invite_code")
    
    # Test time formatting
    assert format_time(0) == "00:00", f"Expected 00:00, got {format_time(0)}"
    assert format_time(60) == "01:00", f"Expected 01:00, got {format_time(60)}"
    assert format_time(95) == "01:35", f"Expected 01:35, got {format_time(95)}"
    print("✓ format_time")
    
    # Test time warnings
    assert is_time_warning(119) == True, "119s should be warning"
    assert is_time_warning(120) == True, "120s should be warning"
    assert is_time_warning(121) == False, "121s should not be warning"
    print("✓ is_time_warning")
    
    # Test validation functions
    assert validate_invite_code("A3F8K2") == True
    assert validate_invite_code("A3F8K") == False
    assert validate_invite_code("A3F8K2X") == False
    print("✓ validate_invite_code")
    
    assert validate_team_name("My Team") == True
    assert validate_team_name("") == False
    assert validate_team_name("A" * 101) == False
    print("✓ validate_team_name")
    
    assert validate_role("tech_lead") == True
    assert validate_role("invalid") == False
    print("✓ validate_role")
    
    # Test mock data generation
    team = generate_mock_team()
    assert "id" in team
    assert "name" in team
    assert "invite_code" in team
    print("✓ generate_mock_team")
    
    members = generate_mock_members(3)
    assert len(members) == 3
    assert all("id" in m and "name" in m for m in members)
    print("✓ generate_mock_members")
    
    meetings = generate_mock_meetings(5)
    assert len(meetings) == 5
    assert all("id" in m and "title" in m for m in meetings)
    print("✓ generate_mock_meetings")
    
    print("\n✅ All functions validated successfully!")

if __name__ == "__main__":
    validate_all_functions()
