package com.standupsync.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "meetings")
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Meeting {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "team_id", nullable = false)
    private Team team;

    @Column(nullable = false)
    private Integer sprintNo;

    @Column(length = 200)
    private String title;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private FormType formType;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private MeetingStatus status;

    @Lob
    @Column(columnDefinition = "TEXT")
    private String aiResult;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private AiStatus aiStatus;

    @Column(length = 1000)
    private String aiError;

    @Column(nullable = false, length = 36)
    private String createdBy;

    @Column(updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime endedAt;

    @Column(nullable = false)
    private Integer countdownSeconds = 900;

    private Integer isArchived = 0;

    private LocalDateTime archivedAt;

    public enum FormType { REALTIME, ASYNC }
    public enum MeetingStatus { CREATED, ACTIVE, ENDED }
    public enum AiStatus { IDLE, PROCESSING, DONE, FAILED }

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) createdAt = LocalDateTime.now();
        if (aiStatus == null) aiStatus = AiStatus.IDLE;
        if (countdownSeconds == null) countdownSeconds = 900;
        if (isArchived == null) isArchived = 0;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Team getTeam() { return team; }
    public void setTeam(Team team) { this.team = team; }
    public Integer getSprintNo() { return sprintNo; }
    public void setSprintNo(Integer sprintNo) { this.sprintNo = sprintNo; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public FormType getFormType() { return formType; }
    public void setFormType(FormType formType) { this.formType = formType; }
    public MeetingStatus getStatus() { return status; }
    public void setStatus(MeetingStatus status) { this.status = status; }
    public String getAiResult() { return aiResult; }
    public void setAiResult(String aiResult) { this.aiResult = aiResult; }
    public AiStatus getAiStatus() { return aiStatus; }
    public void setAiStatus(AiStatus aiStatus) { this.aiStatus = aiStatus; }
    public String getAiError() { return aiError; }
    public void setAiError(String aiError) { this.aiError = aiError; }
    public String getCreatedBy() { return createdBy; }
    public void setCreatedBy(String createdBy) { this.createdBy = createdBy; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getEndedAt() { return endedAt; }
    public void setEndedAt(LocalDateTime endedAt) { this.endedAt = endedAt; }
    public Integer getCountdownSeconds() { return countdownSeconds; }
    public void setCountdownSeconds(Integer countdownSeconds) { this.countdownSeconds = countdownSeconds; }
    public Integer getIsArchived() { return isArchived; }
    public void setIsArchived(Integer isArchived) { this.isArchived = isArchived; }
    public LocalDateTime getArchivedAt() { return archivedAt; }
    public void setArchivedAt(LocalDateTime archivedAt) { this.archivedAt = archivedAt; }
}
