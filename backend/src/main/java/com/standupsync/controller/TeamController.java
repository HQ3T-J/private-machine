package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.Team;
import com.standupsync.model.TeamMember;
import com.standupsync.model.TeamMemberId;
import com.standupsync.model.User;
import com.standupsync.repository.TeamRepository;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.repository.UserRepository;

import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/teams")
public class TeamController {

    private final TeamRepository teamRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final UserRepository userRepository;

    public TeamController(TeamRepository teamRepository,
                          TeamMemberRepository teamMemberRepository,
                          UserRepository userRepository) {
        this.teamRepository = teamRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.userRepository = userRepository;
    }

    @GetMapping
    public ApiResponse<List<Team>> listTeams(@RequestAttribute("userId") String userId) {
        List<Long> teamIds = teamMemberRepository.findByUserId(userId)
                .stream().map(TeamMember::getTeamId).toList();
        if (teamIds.isEmpty()) return ApiResponse.ok(Collections.emptyList());
        return ApiResponse.ok(teamRepository.findAllById(teamIds));
    }

    @PostMapping
    public ApiResponse<Team> createTeam(@RequestAttribute("userId") String userId,
                                        @RequestBody Map<String, String> body) {
        String name = body.get("name");
        if (name == null || name.trim().isEmpty()) {
            return ApiResponse.error(400, "团队名称不能为空");
        }
        Team team = new Team();
        team.setName(name.trim());
        team.setCreatedBy(userId);
        team.setInviteCode(UUID.randomUUID().toString().substring(0, 6).toUpperCase());
        team = teamRepository.save(team);

        TeamMember member = new TeamMember();
        member.setTeamId(team.getId());
        member.setUserId(userId);
        member.setRole(TeamMember.MemberRole.TECH_LEAD);
        teamMemberRepository.save(member);

        return ApiResponse.ok(team);
    }

    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> getTeam(@PathVariable Long id) {
        Team team = teamRepository.findById(id).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        List<TeamMember> members = teamMemberRepository.findByTeamId(id);

        List<Map<String, Object>> memberList = new ArrayList<>();
        for (TeamMember m : members) {
            User user = userRepository.findById(m.getUserId()).orElse(null);
            Map<String, Object> mm = new LinkedHashMap<>();
            mm.put("id", m.getUserId());  // 兼容前端 id 字段
            mm.put("user_id", m.getUserId());
            mm.put("role", m.getRole().name());
            if (user != null) {
                mm.put("username", user.getUsername());
                mm.put("name", user.getDisplayName() != null ? user.getDisplayName() : user.getUsername());
                mm.put("display_name", user.getDisplayName());
            }
            memberList.add(mm);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("team", team);
        result.put("members", memberList);
        return ApiResponse.ok(result);
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> deleteTeam(@RequestAttribute("userId") String userId,
                                        @PathVariable Long id) {
        TeamMember self = teamMemberRepository.findByTeamIdAndUserId(id, userId).orElse(null);
        if (self == null || self.getRole() != TeamMember.MemberRole.TECH_LEAD) {
            return ApiResponse.error(403, "仅 Tech Lead 可删除团队");
        }
        teamRepository.deleteById(id);
        return ApiResponse.ok("团队已删除", null);
    }

    @PostMapping("/{id}/invite")
    public ApiResponse<Map<String, String>> generateInvite(@RequestAttribute("userId") String userId,
                                                            @PathVariable Long id) {
        Team team = teamRepository.findById(id).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        String code = UUID.randomUUID().toString().substring(0, 6).toUpperCase();
        team.setInviteCode(code);
        teamRepository.save(team);
        return ApiResponse.ok(Map.of("code", code));
    }

    @PostMapping("/join")
    public ApiResponse<Team> joinTeam(@RequestAttribute("userId") String userId,
                                      @RequestBody Map<String, String> body) {
        String code = body.get("code");
        Team team = teamRepository.findByInviteCode(code).orElse(null);
        if (team == null) return ApiResponse.error(400, "邀请码无效");

        if (teamMemberRepository.existsByTeamIdAndUserId(team.getId(), userId)) {
            return ApiResponse.error(400, "已在团队中");
        }

        TeamMember member = new TeamMember();
        member.setTeamId(team.getId());
        member.setUserId(userId);
        member.setRole(TeamMember.MemberRole.DEVELOPER);
        teamMemberRepository.save(member);

        return ApiResponse.ok("加入成功", team);
    }

    @DeleteMapping("/{id}/members/{uid}")
    public ApiResponse<Void> removeMember(@RequestAttribute("userId") String userId,
                                          @PathVariable Long id,
                                          @PathVariable String uid) {
        TeamMember self = teamMemberRepository.findByTeamIdAndUserId(id, userId).orElse(null);
        if (self == null) return ApiResponse.error(403, "无权限");
        TeamMember.MemberRole role = self.getRole();
        if (role != TeamMember.MemberRole.TECH_LEAD && role != TeamMember.MemberRole.SCRUM_MASTER) {
            return ApiResponse.error(403, "仅 Tech Lead 或 Scrum Master 可移除成员");
        }
        teamMemberRepository.deleteByTeamIdAndUserId(id, uid);
        return ApiResponse.ok("成员已移除", null);
    }

    @PutMapping("/{id}/members/{uid}/role")
    public ApiResponse<TeamMember> updateRole(@RequestAttribute("userId") String userId,
                                               @PathVariable Long id,
                                               @PathVariable String uid,
                                               @RequestBody Map<String, String> body) {
        TeamMember self = teamMemberRepository.findByTeamIdAndUserId(id, userId).orElse(null);
        if (self == null || self.getRole() != TeamMember.MemberRole.TECH_LEAD) {
            return ApiResponse.error(403, "仅 Tech Lead 可修改角色");
        }
        TeamMember member = teamMemberRepository.findByTeamIdAndUserId(id, uid).orElse(null);
        if (member == null) return ApiResponse.error(404, "成员不存在");
        member.setRole(TeamMember.MemberRole.valueOf(body.get("role").toUpperCase()));
        teamMemberRepository.save(member);
        return ApiResponse.ok(member);
    }
}
