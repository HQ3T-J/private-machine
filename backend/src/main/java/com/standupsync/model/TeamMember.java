package com.standupsync.model;

import jakarta.persistence.*;

@Entity
@Table(name = "team_members")
@IdClass(TeamMemberId.class)
public class TeamMember {

    @Id
    @Column(nullable = false)
    private Long teamId;

    @Id
    @Column(nullable = false, length = 36)
    private String userId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private MemberRole role;

    public enum MemberRole {
        TECH_LEAD, SCRUM_MASTER, DEVELOPER, OBSERVER
    }

    public TeamMember() {}

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public MemberRole getRole() { return role; }
    public void setRole(MemberRole role) { this.role = role; }
}
