package com.standupsync.dto;

import java.util.List;

/**
 * 创建站会请求 DTO
 */
public class CreateStandupDTO {

    private Long teamId;
    private Integer sprint;
    private String mode = "live";     // live / async
    private List<Long> memberIds;     // 指定参与者，null=全部成员

    public CreateStandupDTO() {}

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }

    public Integer getSprint() { return sprint; }
    public void setSprint(Integer sprint) { this.sprint = sprint; }

    public String getMode() { return mode; }
    public void setMode(String mode) { this.mode = mode; }

    public List<Long> getMemberIds() { return memberIds; }
    public void setMemberIds(List<Long> memberIds) { this.memberIds = memberIds; }
}
