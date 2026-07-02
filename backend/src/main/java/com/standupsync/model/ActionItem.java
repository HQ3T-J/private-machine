package com.standupsync.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "action_items")
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class ActionItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "meeting_id")
    private Meeting meeting;

    @Lob
    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "assignee_id")
    private User assignee;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "assigner_id", nullable = false)
    private User assigner;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "team_id", nullable = false)
    private Team team;

    private LocalDate dueDate;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private ActionItemStatus status;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private Priority priority;

    @Column(updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime completedAt;

    @Column(nullable = false)
    private Boolean confirmed = false;

    // ═══════════════════════════════════════════════
    //  转交审批流字段（方案 A：To-Do Module 接入）
    // ═══════════════════════════════════════════════

    @Enumerated(EnumType.STRING)
    @Column(name = "transfer_status", length = 20)
    private TransferStatus transferStatus = TransferStatus.NONE;

    @Column(name = "transfer_reason", columnDefinition = "TEXT")
    private String transferReason;

    @Column(name = "pending_assignee_id", length = 36)
    private String pendingAssigneeId;

    @Column(name = "original_assignee_id", length = 36)
    private String originalAssigneeId;

    @Column(name = "transferred_by", length = 36)
    private String transferredBy;

    @Column(name = "transfer_approved_by", length = 36)
    private String transferApprovedBy;

    @Column(name = "transfer_approved_at")
    private LocalDateTime transferApprovedAt;

    @Column(name = "reject_reason", columnDefinition = "TEXT")
    private String rejectReason;

    @Column(name = "transfer_record_hidden", nullable = false)
    private Boolean transferRecordHidden = false;

    // ═══════════════════════════════════════════════
    //  枚举
    // ═══════════════════════════════════════════════

    public enum ActionItemStatus {
        PENDING, IN_PROGRESS, REVIEWING, DONE, CANCELLED
    }

    public enum Priority {
        HIGH, MEDIUM, LOW
    }

    public enum TransferStatus {
        NONE, PENDING, APPROVED, REJECTED
    }

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (status == null) status = ActionItemStatus.PENDING;
        if (priority == null) priority = Priority.MEDIUM;
        if (transferStatus == null) transferStatus = TransferStatus.NONE;
        if (transferRecordHidden == null) transferRecordHidden = false;
        if (confirmed == null) confirmed = false;
    }

    public ActionItem() {}

    // ═══════════════════════════════════════════════
    //  原有 getter/setter
    // ═══════════════════════════════════════════════

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Meeting getMeeting() { return meeting; }
    public void setMeeting(Meeting meeting) { this.meeting = meeting; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public User getAssignee() { return assignee; }
    public void setAssignee(User assignee) { this.assignee = assignee; }

    public User getAssigner() { return assigner; }
    public void setAssigner(User assigner) { this.assigner = assigner; }

    public Team getTeam() { return team; }
    public void setTeam(Team team) { this.team = team; }

    public LocalDate getDueDate() { return dueDate; }
    public void setDueDate(LocalDate dueDate) { this.dueDate = dueDate; }

    public ActionItemStatus getStatus() { return status; }
    public void setStatus(ActionItemStatus status) { this.status = status; }

    public Priority getPriority() { return priority; }
    public void setPriority(Priority priority) { this.priority = priority; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getCompletedAt() { return completedAt; }
    public void setCompletedAt(LocalDateTime completedAt) { this.completedAt = completedAt; }

    public Boolean getConfirmed() { return confirmed; }
    public void setConfirmed(Boolean confirmed) { this.confirmed = confirmed; }

    // ═══════════════════════════════════════════════
    //  转交审批流 getter/setter
    // ═══════════════════════════════════════════════

    public TransferStatus getTransferStatus() { return transferStatus; }
    public void setTransferStatus(TransferStatus transferStatus) { this.transferStatus = transferStatus; }

    public String getTransferReason() { return transferReason; }
    public void setTransferReason(String transferReason) { this.transferReason = transferReason; }

    public String getPendingAssigneeId() { return pendingAssigneeId; }
    public void setPendingAssigneeId(String pendingAssigneeId) { this.pendingAssigneeId = pendingAssigneeId; }

    public String getOriginalAssigneeId() { return originalAssigneeId; }
    public void setOriginalAssigneeId(String originalAssigneeId) { this.originalAssigneeId = originalAssigneeId; }

    public String getTransferredBy() { return transferredBy; }
    public void setTransferredBy(String transferredBy) { this.transferredBy = transferredBy; }

    public String getTransferApprovedBy() { return transferApprovedBy; }
    public void setTransferApprovedBy(String transferApprovedBy) { this.transferApprovedBy = transferApprovedBy; }

    public LocalDateTime getTransferApprovedAt() { return transferApprovedAt; }
    public void setTransferApprovedAt(LocalDateTime transferApprovedAt) { this.transferApprovedAt = transferApprovedAt; }

    public String getRejectReason() { return rejectReason; }
    public void setRejectReason(String rejectReason) { this.rejectReason = rejectReason; }

    public Boolean getTransferRecordHidden() { return transferRecordHidden; }
    public void setTransferRecordHidden(Boolean transferRecordHidden) { this.transferRecordHidden = transferRecordHidden; }
}
