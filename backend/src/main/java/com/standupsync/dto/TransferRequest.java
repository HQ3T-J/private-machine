package com.standupsync.dto;

public class TransferRequest {

    private String targetUserId;
    private String reason;

    public TransferRequest() {}

    public TransferRequest(String targetUserId, String reason) {
        this.targetUserId = targetUserId;
        this.reason = reason;
    }

    public String getTargetUserId() { return targetUserId; }
    public void setTargetUserId(String targetUserId) { this.targetUserId = targetUserId; }

    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
}
