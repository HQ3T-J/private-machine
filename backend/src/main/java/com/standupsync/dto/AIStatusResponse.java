package com.standupsync.dto;

import java.util.Map;

/**
 * DTO for AI analysis status response.
 */
public class AIStatusResponse {

    private Long meetingId;
    private String status;       // PENDING | ANALYZING | COMPLETED | FAILED
    private String error;
    private String partialResult; // available when FAILED with partial output

    public AIStatusResponse() {}

    public AIStatusResponse(Long meetingId, String status) {
        this.meetingId = meetingId;
        this.status = status;
    }

    public Long getMeetingId() { return meetingId; }
    public void setMeetingId(Long meetingId) { this.meetingId = meetingId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
    public String getPartialResult() { return partialResult; }
    public void setPartialResult(String partialResult) { this.partialResult = partialResult; }
}
