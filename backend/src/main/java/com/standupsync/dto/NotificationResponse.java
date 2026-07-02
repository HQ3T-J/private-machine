package com.standupsync.dto;

import com.standupsync.model.Notification;

import java.time.LocalDateTime;

public class NotificationResponse {

    private Long id;
    private String userId;
    private Long teamId;
    private String type;
    private String content;
    private Long relatedItemId;
    private String senderId;
    private Boolean isRead;
    private LocalDateTime createdAt;

    public NotificationResponse() {}

    public static NotificationResponse fromEntity(Notification n) {
        NotificationResponse r = new NotificationResponse();
        r.id = n.getId();
        r.userId = n.getUserId();
        r.teamId = n.getTeamId();
        r.type = n.getType() != null ? n.getType().name() : null;
        r.content = n.getContent();
        r.relatedItemId = n.getRelatedItemId();
        r.senderId = n.getSenderId();
        r.isRead = n.getIsRead();
        r.createdAt = n.getCreatedAt();
        return r;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public Long getRelatedItemId() { return relatedItemId; }
    public void setRelatedItemId(Long relatedItemId) { this.relatedItemId = relatedItemId; }

    public String getSenderId() { return senderId; }
    public void setSenderId(String senderId) { this.senderId = senderId; }

    public Boolean getIsRead() { return isRead; }
    public void setIsRead(Boolean isRead) { this.isRead = isRead; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
