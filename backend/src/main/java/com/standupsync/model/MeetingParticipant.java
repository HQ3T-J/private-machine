package com.standupsync.model;

import jakarta.persistence.*;

@Entity
@Table(name = "meeting_participants")
@IdClass(MeetingParticipantId.class)
public class MeetingParticipant {

    @Id
    @Column(nullable = false)
    private Long meetingId;

    @Id
    @Column(nullable = false, length = 36)
    private String userId;

    private Integer speechOrder;

    @Column(nullable = false)
    private Boolean hasSpoken = false;

    public MeetingParticipant() {}

    public Long getMeetingId() { return meetingId; }
    public void setMeetingId(Long meetingId) { this.meetingId = meetingId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Integer getSpeechOrder() { return speechOrder; }
    public void setSpeechOrder(Integer speechOrder) { this.speechOrder = speechOrder; }

    public Boolean getHasSpoken() { return hasSpoken; }
    public void setHasSpoken(Boolean hasSpoken) { this.hasSpoken = hasSpoken; }
}
