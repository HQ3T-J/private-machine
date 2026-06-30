package com.standupsync.dto;

import jakarta.validation.constraints.NotBlank;
import java.time.LocalDate;

public class ActionItemRequest {

    private Long id;

    @NotBlank(message = "content is required")
    private String content;

    private Long assigneeId;
    private String assigneeName;
    private String status = "TODO";
    private String priority = "MEDIUM";
    private LocalDate dueDate;
    private Boolean confirmed = false;

    public ActionItemRequest() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public Long getAssigneeId() { return assigneeId; }
    public void setAssigneeId(Long assigneeId) { this.assigneeId = assigneeId; }
    public String getAssigneeName() { return assigneeName; }
    public void setAssigneeName(String assigneeName) { this.assigneeName = assigneeName; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getPriority() { return priority; }
    public void setPriority(String priority) { this.priority = priority; }
    public LocalDate getDueDate() { return dueDate; }
    public void setDueDate(LocalDate dueDate) { this.dueDate = dueDate; }
    public Boolean getConfirmed() { return confirmed; }
    public void setConfirmed(Boolean confirmed) { this.confirmed = confirmed; }
}
