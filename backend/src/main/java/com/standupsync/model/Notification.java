package com.standupsync.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "notifications")
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 36)
    private String userId;

    @Column(nullable = false)
    private Long teamId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private NotificationType type;

    @Lob
    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(nullable = true)
    private Long relatedItemId;

    @Column(nullable = false, length = 36)
    private String senderId;

    @Column(nullable = false)
    private Boolean isRead = false;

    @CreationTimestamp
    @Column(updatable = false, nullable = false)
    private LocalDateTime createdAt;

    // ═══════════════════════════════════════════════
    //  枚举
    // ═══════════════════════════════════════════════

    public enum NotificationType {
        TODO_ASSIGNED,
        TODO_TRANSFERRED,
        TODO_COMPLETED,
        TRANSFER_APPROVED,
        TRANSFER_REJECTED
    }

    public Notification() {}

    // ═══════════════════════════════════════════════
    //  getter/setter
    // ═══════════════════════════════════════════════

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }

    public NotificationType getType() { return type; }
    public void setType(NotificationType type) { this.type = type; }

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
