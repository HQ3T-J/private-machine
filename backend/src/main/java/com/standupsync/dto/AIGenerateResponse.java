package com.standupsync.dto;

import java.util.List;

public class AIGenerateResponse {

    private List<GeneratedTodo> todos;
    private String summary;

    public AIGenerateResponse() {}

    public AIGenerateResponse(List<GeneratedTodo> todos, String summary) {
        this.todos = todos;
        this.summary = summary;
    }

    // ═══════════════════════════════════════════════
    //  Inner class: GeneratedTodo
    // ═══════════════════════════════════════════════

    public static class GeneratedTodo {
        private String content;
        private String priority;
        private String suggestedAssignee;

        public GeneratedTodo() {}

        public GeneratedTodo(String content, String priority, String suggestedAssignee) {
            this.content = content;
            this.priority = priority;
            this.suggestedAssignee = suggestedAssignee;
        }

        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }

        public String getPriority() { return priority; }
        public void setPriority(String priority) { this.priority = priority; }

        public String getSuggestedAssignee() { return suggestedAssignee; }
        public void setSuggestedAssignee(String suggestedAssignee) { this.suggestedAssignee = suggestedAssignee; }
    }

    // ═══════════════════════════════════════════════
    //  getter/setter
    // ═══════════════════════════════════════════════

    public List<GeneratedTodo> getTodos() { return todos; }
    public void setTodos(List<GeneratedTodo> todos) { this.todos = todos; }

    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }
}
