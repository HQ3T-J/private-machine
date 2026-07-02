package com.standup.todo.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class TodoRequest {
    private String content;
    private String assigneeId;
    private LocalDateTime dueDate;
    private String priority = "MEDIUM";
    private String teamId;
}
