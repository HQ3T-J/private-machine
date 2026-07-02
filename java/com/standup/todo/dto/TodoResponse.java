package com.standup.todo.dto;

import lombok.Data;
import lombok.Builder;

import java.time.LocalDateTime;

@Data
@Builder
public class TodoResponse {
    private Long id;
    private String content;
    private String assigneeId;
    private String creatorId;
    private LocalDateTime dueDate;
    private String priority;
    private String status;
    private String teamId;
    private LocalDateTime createdAt;
    private LocalDateTime completedAt;
    private String transferReason;
    private String pendingAssigneeId;
    private String originalAssigneeId;
    private String transferredBy;
    private String transferStatus;
    private String transferApprovedBy;
    private LocalDateTime transferApprovedAt;
    private String rejectReason;
    private boolean isOverdue;
    private boolean isDueSoon;
    private boolean hasPermission;
    private boolean pendingTransfer;
}
