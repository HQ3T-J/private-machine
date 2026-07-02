package com.standup.todo.dto;

import lombok.Data;
import lombok.Builder;
import java.util.List;

@Data
@Builder
public class AIGenerateResponse {
    private List<GeneratedTodo> todos;
    private String summary;

    @Data
    @Builder
    public static class GeneratedTodo {
        private String content;
        private String priority; // HIGH, MEDIUM, LOW
        private String suggestedAssignee; // 建议的责任人（可选）
    }
}
