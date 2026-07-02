package com.standup.todo.entity;

import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "notifications")
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, length = 50)
    private String userId;

    @Column(name = "team_id", nullable = false, length = 50)
    private String teamId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private NotificationType type;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "related_todo_id")
    private Long relatedTodoId;

    @Column(name = "sender_id", length = 50)
    private String senderId;

    @Column(name = "is_read", nullable = false)
    private Boolean isRead = false;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    public enum NotificationType {
        TODO_ASSIGNED,      // 待办分配
        TODO_TRANSFERRED,   // 待办转交
        TODO_COMPLETED,     // 待办完成
        TRANSFER_APPROVED,  // 转交批准
        TRANSFER_REJECTED   // 转交拒绝
    }
}
