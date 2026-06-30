package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.*;
import com.standupsync.repository.*;

import org.springframework.web.bind.annotation.*;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@RestController
@RequestMapping("/api/teams")
public class TeamController {

    private final TeamRepository teamRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final TeamApplicationRepository applicationRepository;
    private final UserRepository userRepository;

    public TeamController(TeamRepository teamRepository,
                          TeamMemberRepository teamMemberRepository,
                          TeamApplicationRepository applicationRepository,
                          UserRepository userRepository) {
        this.teamRepository = teamRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.applicationRepository = applicationRepository;
        this.userRepository = userRepository;
    }

    // ═══ 创建团队 ═══
    @PostMapping
    @Transactional
    public ApiResponse<Team> createTeam(@RequestAttribute("userId") String userId,
                                         @RequestBody Map<String, String> body) {
        String name = body.getOrDefault("name", "").trim();
        if (name.isEmpty()) return ApiResponse.error(400, "团队名称不能为空");

        Team team = new Team();
        team.setName(name);
        team.setCreatedBy(userId);
        team.setInviteCode(generateCode());
        team = teamRepository.save(team);

        TeamMember member = new TeamMember();
        member.setTeamId(team.getId());
        member.setUserId(userId);
        member.setRole(TeamMember.MemberRole.TECH_LEAD);
        teamMemberRepository.save(member);

        return ApiResponse.success("团队创建成功", team);
    }

    // ═══ 团队列表 ═══
    @GetMapping
    public ApiResponse<List<Team>> listTeams(@RequestAttribute("userId") String userId) {
        List<TeamMember> memberships = teamMemberRepository.findByUserId(userId);
        List<Team> teams = new ArrayList<>();
        for (TeamMember m : memberships) {
            teamRepository.findById(m.getTeamId()).ifPresent(teams::add);
        }
        return ApiResponse.success(teams);
    }

    // ═══ 团队详情(含成员) ═══
    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> getTeam(@PathVariable Long id) {
        Team team = teamRepository.findById(id).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");

        List<TeamMember> members = teamMemberRepository.findByTeamId(id);
        List<Map<String, Object>> memberList = new ArrayList<>();
        for (TeamMember m : members) {
            User user = userRepository.findById(m.getUserId()).orElse(null);
            Map<String, Object> pm = new LinkedHashMap<>();
            pm.put("id", m.getTeamId());
            pm.put("user_id", m.getUserId());
            pm.put("role", m.getRole().name());
            pm.put("role_level", roleToLevel(m.getRole()));
            if (user != null) {
                pm.put("username", user.getUsername());
                pm.put("name", user.getDisplayName());
            }
            memberList.add(pm);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("team", team);
        result.put("members", memberList);
        return ApiResponse.success(result);
    }

    // ═══ 申请加入 ═══
    @PostMapping("/join")
    public ApiResponse<?> applyToJoin(@RequestAttribute("userId") String userId,
                                       @RequestBody Map<String, String> body) {
        String code = body.getOrDefault("inviteCode", "").trim();
        Team team = teamRepository.findByInviteCode(code).orElse(null);
        if (team == null) return ApiResponse.error(404, "邀请码无效");

        // 检查是否已是成员
        if (teamMemberRepository.existsByTeamIdAndUserId(team.getId(), userId))
            return ApiResponse.error(400, "你已经是团队成员");

        // 检查是否已有待审批申请
        if (applicationRepository.existsByTeamIdAndUserIdAndStatus(team.getId(), userId, 0))
            return ApiResponse.error(400, "已提交申请，请等待团长审核");

        TeamApplication app = new TeamApplication();
        app.setTeamId(team.getId());
        app.setUserId(userId);
        app.setStatus(0);
        applicationRepository.save(app);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("teamId", team.getId());
        data.put("teamName", team.getName());
        return ApiResponse.success("申请已提交，等待团长审核", data);
    }

    // ═══ 审批列表(团长/ScrumMaster) ═══
    @GetMapping("/{id}/applications")
    public ApiResponse<?> getApplications(@RequestAttribute("userId") String userId,
                                           @PathVariable Long id) {
        if (!isMasterOrScrumMaster(id, userId))
            return ApiResponse.error(403, "只有团长或Scrum Master可以查看申请列表");

        List<TeamApplication> list = applicationRepository.findByTeamIdAndStatus(id, 0);
        List<Map<String, Object>> result = new ArrayList<>();
        for (TeamApplication a : list) {
            User user = userRepository.findById(a.getUserId()).orElse(null);
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("id", a.getId());
            map.put("teamId", a.getTeamId());
            map.put("userId", a.getUserId());
            map.put("status", a.getStatus());
            map.put("createdAt", a.getCreatedAt());
            map.put("name", user != null ? user.getDisplayName() : "?");
            result.add(map);
        }
        return ApiResponse.success(result);
    }

    // ═══ 批准申请 ═══
    @PostMapping("/{id}/applications/{appId}/approve")
    @Transactional
    public ApiResponse<?> approveApplication(@RequestAttribute("userId") String userId,
                                              @PathVariable Long id,
                                              @PathVariable Long appId) {
        if (!isMasterOrScrumMaster(id, userId))
            return ApiResponse.error(403, "只有团长或Scrum Master可以审核");

        TeamApplication app = applicationRepository.findById(appId).orElse(null);
        if (app == null || !app.getTeamId().equals(id))
            return ApiResponse.error(404, "申请不存在");
        if (app.getStatus() != 0)
            return ApiResponse.error(400, "申请已处理");

        app.setStatus(1);
        applicationRepository.save(app);

        TeamMember member = new TeamMember();
        member.setTeamId(id);
        member.setUserId(app.getUserId());
        member.setRole(TeamMember.MemberRole.DEVELOPER);
        teamMemberRepository.save(member);

        return ApiResponse.success("已通过");
    }

    // ═══ 拒绝申请 ═══
    @PostMapping("/{id}/applications/{appId}/reject")
    public ApiResponse<?> rejectApplication(@RequestAttribute("userId") String userId,
                                             @PathVariable Long id,
                                             @PathVariable Long appId) {
        if (!isMasterOrScrumMaster(id, userId))
            return ApiResponse.error(403, "只有团长或Scrum Master可以审核");

        TeamApplication app = applicationRepository.findById(appId).orElse(null);
        if (app == null || !app.getTeamId().equals(id))
            return ApiResponse.error(404, "申请不存在");

        app.setStatus(2);
        applicationRepository.save(app);
        return ApiResponse.success("已拒绝");
    }

    // ═══ 修改角色(仅团长) ═══
    @PutMapping("/{id}/members/{uid}/role")
    public ApiResponse<?> changeRole(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id,
                                      @PathVariable String uid,
                                      @RequestBody Map<String, String> body) {
        if (!isTechLead(id, userId))
            return ApiResponse.error(403, "只有技术主管可以修改角色");

        String newRole = body.getOrDefault("role", "").toUpperCase();
        TeamMember.MemberRole role;
        try { role = TeamMember.MemberRole.valueOf(newRole); }
        catch (IllegalArgumentException e) { return ApiResponse.error(400, "无效角色: " + newRole); }

        TeamMember member = teamMemberRepository.findByTeamIdAndUserId(id, uid).orElse(null);
        if (member == null || !member.getTeamId().equals(id))
            return ApiResponse.error(404, "成员不存在");
        if (member.getUserId().equals(userId))
            return ApiResponse.error(400, "不能修改自己的角色");

        // 如果降级的是最后一个团长
        if (member.getRole() == TeamMember.MemberRole.TECH_LEAD && role != TeamMember.MemberRole.TECH_LEAD) {
            if (countTechLeads(id) <= 1)
                return ApiResponse.error(400, "团队至少需要一名技术主管，不能降级");
        }

        member.setRole(role);
        teamMemberRepository.save(member);
        return ApiResponse.success("角色已更新");
    }

    // ═══ 移除成员 ═══
    @DeleteMapping("/{id}/members/{uid}")
    public ApiResponse<?> removeMember(@RequestAttribute("userId") String userId,
                                        @PathVariable Long id,
                                        @PathVariable String uid) {
        if (!isMasterOrScrumMaster(id, userId))
            return ApiResponse.error(403, "只有技术主管或Scrum Master可以移除成员");

        if (uid.equals(userId))
            return ApiResponse.error(400, "不能移除自己");

        TeamMember member = teamMemberRepository.findByTeamIdAndUserId(id, uid).orElse(null);
        if (member == null) return ApiResponse.error(404, "成员不存在");

        if (member.getRole() == TeamMember.MemberRole.TECH_LEAD && countTechLeads(id) <= 1)
            return ApiResponse.error(400, "团队至少需要一名技术主管，不能移除最后一位");

        teamMemberRepository.delete(member);
        return ApiResponse.success("成员已移除");
    }

    // ═══ 修改队名(仅团长) ═══
    @PutMapping("/{id}")
    public ApiResponse<?> updateName(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id,
                                      @RequestBody Map<String, String> body) {
        if (!isTechLead(id, userId))
            return ApiResponse.error(403, "只有技术主管可以修改团队名称");

        String name = body.getOrDefault("name", "").trim();
        if (name.isEmpty()) return ApiResponse.error(400, "名称不能为空");

        Team team = teamRepository.findById(id).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        team.setName(name);
        teamRepository.save(team);
        return ApiResponse.success("团队名称已更新");
    }

    // ═══ 重生成邀请码(仅团长) ═══
    @PostMapping("/{id}/invite-code")
    public ApiResponse<?> regenerateCode(@RequestAttribute("userId") String userId,
                                          @PathVariable Long id) {
        if (!isTechLead(id, userId))
            return ApiResponse.error(403, "只有技术主管可以重新生成邀请码");

        Team team = teamRepository.findById(id).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        team.setInviteCode(generateCode());
        teamRepository.save(team);
        return ApiResponse.success(team.getInviteCode());
    }

    // ═══ 解散团队(仅团长) ═══
    @PostMapping("/{id}/dissolve")
    @Transactional
    public ApiResponse<?> dissolve(@RequestAttribute("userId") String userId,
                                    @PathVariable Long id) {
        if (!isTechLead(id, userId))
            return ApiResponse.error(403, "只有技术主管可以解散团队");

        teamRepository.deleteById(id);
        return ApiResponse.success("团队已解散");
    }

    // ═══ 获取邀请码 ═══
    @PostMapping("/{id}/invite")
    public ApiResponse<?> getInviteCode(@PathVariable Long id) {
        Team team = teamRepository.findById(id).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        return ApiResponse.success(team.getInviteCode());
    }

    // ── helpers ──

    private boolean isTechLead(Long teamId, String userId) {
        return teamMemberRepository.findByTeamIdAndUserId(teamId, userId)
                .map(m -> m.getRole() == TeamMember.MemberRole.TECH_LEAD).orElse(false);
    }

    private boolean isMasterOrScrumMaster(Long teamId, String userId) {
        return teamMemberRepository.findByTeamIdAndUserId(teamId, userId)
                .map(m -> m.getRole() == TeamMember.MemberRole.TECH_LEAD
                       || m.getRole() == TeamMember.MemberRole.SCRUM_MASTER).orElse(false);
    }

    private int countTechLeads(Long teamId) {
        return (int) teamMemberRepository.findByTeamId(teamId).stream()
                .filter(m -> m.getRole() == TeamMember.MemberRole.TECH_LEAD).count();
    }

    private int roleToLevel(TeamMember.MemberRole role) {
        return switch (role) {
            case TECH_LEAD -> 2;
            case SCRUM_MASTER -> 1;
            default -> 0;
        };
    }

    private String generateCode() {
        return String.format("%06d", new java.util.Random().nextInt(1000000));
    }
}
