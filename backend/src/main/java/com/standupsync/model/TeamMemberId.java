package com.standupsync.model;

import java.io.Serializable;
import java.util.Objects;

public class TeamMemberId implements Serializable {

    private Long teamId;
    private String userId;

    public TeamMemberId() {}

    public TeamMemberId(Long teamId, String userId) {
        this.teamId = teamId;
        this.userId = userId;
    }

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        TeamMemberId that = (TeamMemberId) o;
        return Objects.equals(teamId, that.teamId) && Objects.equals(userId, that.userId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(teamId, userId);
    }
}
