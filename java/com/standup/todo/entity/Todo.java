package com.standup.todo.entity;

import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "todos")
public class Todo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "assignee_id", nullable = false, length = 50)
    private String assigneeId;

    @Column(name = "creator_id", nullable = false, length = 50)
    private String creatorId;

    @Column(name = "due_date")
    private LocalDateTime dueDate;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Priority priority = Priority.MEDIUM;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status = Status.PENDING;

    @Column(name = "team_id", nullable = false, length = 50)
    private String teamId;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Column(name = "transfer_reason", columnDefinition = "TEXT")
    private String transferReason;

    @Column(name = "pending_assignee_id", length = 50)
    private String pendingAssigneeId;

    @Column(name = "original_assignee_id", length = 50)
    private String originalAssigneeId;

    @Column(name = "transferred_by", length = 50)
    private String transferredBy;

    @Enumerated(EnumType.STRING)
    @Column(name = "transfer_status")
    private TransferStatus transferStatus;

    @Column(name = "transfer_approved_by", length = 50)
    private String transferApprovedBy;

    @Column(name = "transfer_approved_at")
    private LocalDateTime transferApprovedAt;

    @Column(name = "reject_reason", columnDefinition = "TEXT")
    private String rejectReason;

    @Column(name = "transfer_record_hidden", nullable = false, columnDefinition = "BOOLEAN DEFAULT FALSE")
    private Boolean transferRecordHidden = false;

    @Column(name = "is_deleted", nullable = false)
    private Boolean isDeleted = false;

    @PrePersist
    public void prePersist() {
        if (transferRecordHidden == null) {
            transferRecordHidden = false;
        }
        if (isDeleted == null) {
            isDeleted = false;
        }
    }

    @PreUpdate
    public void preUpdate() {
        if (transferRecordHidden == null) {
            transferRecordHidden = false;
        }
        if (isDeleted == null) {
            isDeleted = false;
        }
    }

    public enum TransferStatus {
        NONE, PENDING, APPROVED, REJECTED
    }

    public enum Priority {
        HIGH, MEDIUM, LOW
    }

    public enum Status {
        PENDING, IN_PROGRESS, COMPLETED, REVIEWING
    }
}
