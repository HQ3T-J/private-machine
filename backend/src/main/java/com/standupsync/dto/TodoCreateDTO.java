package com.standupsync.dto;

/**
 * 待办创建 DTO
 */
public class TodoCreateDTO {

    private String content;
    private Long teamId;
    private String priority = "MEDIUM";
    private Long assigneeId;
    private String dueDate;
    private Long meetingId;

    public TodoCreateDTO() {}

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }

    public String getPriority() { return priority; }
    public void setPriority(String priority) { this.priority = priority; }

    public Long getAssigneeId() { return assigneeId; }
    public void setAssigneeId(Long assigneeId) { this.assigneeId = assigneeId; }

    public String getDueDate() { return dueDate; }
    public void setDueDate(String dueDate) { this.dueDate = dueDate; }

    public Long getMeetingId() { return meetingId; }
    public void setMeetingId(Long meetingId) { this.meetingId = meetingId; }
}
