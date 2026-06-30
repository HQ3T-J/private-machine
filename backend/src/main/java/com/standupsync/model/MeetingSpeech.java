package com.standupsync.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "meeting_speeches")
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class MeetingSpeech {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "meeting_id", nullable = false)
    private Meeting meeting;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "speaker_id", nullable = false)
    private User speaker;

    @Lob
    @Column(columnDefinition = "TEXT")
    private String yesterday;

    @Lob
    @Column(columnDefinition = "TEXT")
    private String today;

    @Lob
    @Column(columnDefinition = "TEXT")
    private String blockers;

    @Lob
    @Column(columnDefinition = "TEXT")
    private String rawText;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private InputMethod inputMethod;

    @Column(updatable = false)
    private LocalDateTime createdAt;

    public enum InputMethod {
        TEXT, VOICE, PASTE
    }

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    public MeetingSpeech() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Meeting getMeeting() { return meeting; }
    public void setMeeting(Meeting meeting) { this.meeting = meeting; }

    public User getSpeaker() { return speaker; }
    public void setSpeaker(User speaker) { this.speaker = speaker; }

    public String getYesterday() { return yesterday; }
    public void setYesterday(String yesterday) { this.yesterday = yesterday; }

    public String getToday() { return today; }
    public void setToday(String today) { this.today = today; }

    public String getBlockers() { return blockers; }
    public void setBlockers(String blockers) { this.blockers = blockers; }

    public String getRawText() { return rawText; }
    public void setRawText(String rawText) { this.rawText = rawText; }

    public InputMethod getInputMethod() { return inputMethod; }
    public void setInputMethod(InputMethod inputMethod) { this.inputMethod = inputMethod; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
