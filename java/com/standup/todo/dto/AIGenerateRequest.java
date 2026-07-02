package com.standup.todo.dto;

import lombok.Data;

@Data
public class AIGenerateRequest {
    private String content; // 会议内容或需求描述
    private String teamId;  // 团队ID
}
