package com.standupsync.service;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.*;
import com.standupsync.repository.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
public class TeamService {

    private final TeamRepository teamRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final TeamApplicationRepository applicationRepository;
    private final UserRepository userRepository;

    public TeamService(TeamRepository teamRepository,
                       TeamMemberRepository teamMemberRepository,
                       TeamApplicationRepository applicationRepository,
                       UserRepository userRepository) {
        this.teamRepository = teamRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.applicationRepository = applicationRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public ApiResponse<Team> createTeam(String userId, String name) {
        if (name == null || name.trim().isEmpty()) return ApiResponse.error(400, "团队名称不能为空");
        Team team = new Team();
        team.setName(name.trim());
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

    public ApiResponse<List<Team>> listTeams(String userId) {
        List<TeamMember> memberships = teamMemberRepository.findByUserId(userId);
        List<Team> teams = new ArrayList<>();
        for (TeamMember m : memberships)
            teamRepository.findById(m.getTeamId()).ifPresent(teams::add);
        return ApiResponse.success(teams);
    }

    public ApiResponse<Map<String, Object>> getTeam(Long id) {
        Team team = teamRepository.findById(id).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");

        List<TeamMember> members = teamMemberRepository.findByTeamId(id);
        List<Map<String, Object>> memberList = new ArrayList<>();
        for (TeamMember m : members) {
            User user = userRepository.findById(m.getUserId()).orElse(null);
            Map<String, Object> pm = new LinkedHashMap<>();
            pm.put("user_id", m.getUserId());
            pm.put("role", m.getRole().name());
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

    public ApiResponse<?> applyToJoin(String userId, String code) {
        if (code == null || code.trim().isEmpty()) return ApiResponse.error(400, "邀请码不能为空");
        Team team = teamRepository.findByInviteCode(code.trim()).orElse(null);
        if (team == null) return ApiResponse.error(404, "邀请码无效");
        if (teamMemberRepository.existsByTeamIdAndUserId(team.getId(), userId))
            return ApiResponse.error(400, "你已经是团队成员");
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

    public ApiResponse<?> getApplications(String userId, Long teamId) {
        if (!isAdmin(teamId, userId)) return ApiResponse.error(403, "只有团长或Scrum Master可以查看申请");
        List<TeamApplication> list = applicationRepository.findByTeamIdAndStatus(teamId, 0);
        List<Map<String, Object>> result = new ArrayList<>();
        for (TeamApplication a : list) {
            User user = userRepository.findById(a.getUserId()).orElse(null);
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("id", a.getId());
            map.put("userId", a.getUserId());
            map.put("createdAt", a.getCreatedAt());
            map.put("name", user != null ? user.getDisplayName() : "?");
            result.add(map);
        }
        return ApiResponse.success(result);
    }

    @Transactional
    public ApiResponse<?> approveApplication(String userId, Long teamId, Long appId) {
        if (!isAdmin(teamId, userId)) return ApiResponse.error(403, "只有团长或Scrum Master可以审核");
        TeamApplication app = applicationRepository.findById(appId).orElse(null);
        if (app == null || !app.getTeamId().equals(teamId)) return ApiResponse.error(404, "申请不存在");
        if (app.getStatus() != 0) return ApiResponse.error(400, "申请已处理");
        app.setStatus(1);
        applicationRepository.save(app);

        TeamMember member = new TeamMember();
        member.setTeamId(teamId);
        member.setUserId(app.getUserId());
        member.setRole(TeamMember.MemberRole.DEVELOPER);
        teamMemberRepository.save(member);
        return ApiResponse.success("已通过");
    }

    public ApiResponse<?> rejectApplication(String userId, Long teamId, Long appId) {
        if (!isAdmin(teamId, userId)) return ApiResponse.error(403, "只有团长或Scrum Master可以审核");
        TeamApplication app = applicationRepository.findById(appId).orElse(null);
        if (app == null || !app.getTeamId().equals(teamId)) return ApiResponse.error(404, "申请不存在");
        app.setStatus(2);
        applicationRepository.save(app);
        return ApiResponse.success("已拒绝");
    }

    public ApiResponse<?> changeRole(String userId, Long teamId, String uid, String newRole) {
        if (!isTechLead(teamId, userId)) return ApiResponse.error(403, "只有技术主管可以修改角色");
        TeamMember.MemberRole role;
        try { role = TeamMember.MemberRole.valueOf(newRole.toUpperCase()); }
        catch (IllegalArgumentException e) { return ApiResponse.error(400, "无效角色"); }
        TeamMember member = teamMemberRepository.findByTeamIdAndUserId(teamId, uid).orElse(null);
        if (member == null) return ApiResponse.error(404, "成员不存在");
        if (member.getUserId().equals(userId)) return ApiResponse.error(400, "不能修改自己的角色");
        if (member.getRole() == TeamMember.MemberRole.TECH_LEAD && role != TeamMember.MemberRole.TECH_LEAD
                && countTechLeads(teamId) <= 1)
            return ApiResponse.error(400, "团队至少需要一名技术主管");
        member.setRole(role);
        teamMemberRepository.save(member);
        return ApiResponse.success("角色已更新");
    }

    public ApiResponse<?> removeMember(String userId, Long teamId, String uid) {
        if (!isAdmin(teamId, userId)) return ApiResponse.error(403, "只有技术主管或Scrum Master可以移除成员");
        if (uid.equals(userId)) return ApiResponse.error(400, "不能移除自己");
        TeamMember member = teamMemberRepository.findByTeamIdAndUserId(teamId, uid).orElse(null);
        if (member == null) return ApiResponse.error(404, "成员不存在");
        if (member.getRole() == TeamMember.MemberRole.TECH_LEAD && countTechLeads(teamId) <= 1)
            return ApiResponse.error(400, "团队至少需要一名技术主管");
        teamMemberRepository.delete(member);
        return ApiResponse.success("成员已移除");
    }

    public ApiResponse<?> updateName(String userId, Long teamId, String name) {
        if (!isTechLead(teamId, userId)) return ApiResponse.error(403, "只有技术主管可以修改团队名称");
        if (name == null || name.trim().isEmpty()) return ApiResponse.error(400, "名称不能为空");
        Team team = teamRepository.findById(teamId).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        team.setName(name.trim());
        teamRepository.save(team);
        return ApiResponse.success("团队名称已更新");
    }

    public ApiResponse<?> regenerateCode(String userId, Long teamId) {
        if (!isTechLead(teamId, userId)) return ApiResponse.error(403, "只有技术主管可以重新生成邀请码");
        Team team = teamRepository.findById(teamId).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        team.setInviteCode(generateCode());
        teamRepository.save(team);
        return ApiResponse.success(team.getInviteCode());
    }

    @Transactional
    public ApiResponse<?> dissolve(String userId, Long teamId) {
        if (!isTechLead(teamId, userId)) return ApiResponse.error(403, "只有技术主管可以解散团队");
        teamRepository.deleteById(teamId);
        return ApiResponse.success("团队已解散");
    }

    public ApiResponse<?> getInviteCode(Long teamId) {
        Team team = teamRepository.findById(teamId).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");
        return ApiResponse.success(team.getInviteCode());
    }

    private boolean isTechLead(Long teamId, String userId) {
        return teamMemberRepository.findByTeamIdAndUserId(teamId, userId)
                .map(m -> m.getRole() == TeamMember.MemberRole.TECH_LEAD).orElse(false);
    }

    private boolean isAdmin(Long teamId, String userId) {
        return teamMemberRepository.findByTeamIdAndUserId(teamId, userId)
                .map(m -> m.getRole() == TeamMember.MemberRole.TECH_LEAD
                       || m.getRole() == TeamMember.MemberRole.SCRUM_MASTER).orElse(false);
    }

    private int countTechLeads(Long teamId) {
        return (int) teamMemberRepository.findByTeamId(teamId).stream()
                .filter(m -> m.getRole() == TeamMember.MemberRole.TECH_LEAD).count();
    }

    private String generateCode() {
        return String.format("%06d", new Random().nextInt(1000000));
    }
}
