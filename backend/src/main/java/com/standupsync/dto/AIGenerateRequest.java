package com.standupsync.dto;

public class AIGenerateRequest {

    private String content;
    private Long teamId;

    public AIGenerateRequest() {}

    public AIGenerateRequest(String content, Long teamId) {
        this.content = content;
        this.teamId = teamId;
    }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }
}
