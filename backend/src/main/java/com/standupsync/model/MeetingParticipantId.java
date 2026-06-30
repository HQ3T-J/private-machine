package com.standupsync.model;

import java.io.Serializable;
import java.util.Objects;

public class MeetingParticipantId implements Serializable {

    private Long meetingId;
    private String userId;

    public MeetingParticipantId() {}

    public MeetingParticipantId(Long meetingId, String userId) {
        this.meetingId = meetingId;
        this.userId = userId;
    }

    public Long getMeetingId() { return meetingId; }
    public void setMeetingId(Long meetingId) { this.meetingId = meetingId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        MeetingParticipantId that = (MeetingParticipantId) o;
        return Objects.equals(meetingId, that.meetingId) && Objects.equals(userId, that.userId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(meetingId, userId);
    }
}
