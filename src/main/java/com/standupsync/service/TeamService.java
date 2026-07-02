package com.standupsync.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.standupsync.dto.Result;
import com.standupsync.entity.*;
import com.standupsync.mapper.*;
import com.standupsync.websocket.StandupWebSocketHandler;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class TeamService {

    private final TeamMapper teamMapper;
    private final TeamMemberMapper teamMemberMapper;
    private final TeamApplyMapper teamApplyMapper;
    private final UserMapper userMapper;
    private final StandupWebSocketHandler wsHandler;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // Role constants
    public static final int ROLE_MASTER = 2;   // 团长
    public static final int ROLE_ADMIN = 1;    // 管理员
    public static final int ROLE_MEMBER = 0;   // 普通团员

    public TeamService(TeamMapper teamMapper, TeamMemberMapper teamMemberMapper,
                       TeamApplyMapper teamApplyMapper, UserMapper userMapper,
                       StandupWebSocketHandler wsHandler) {
        this.teamMapper = teamMapper;
        this.teamMemberMapper = teamMemberMapper;
        this.teamApplyMapper = teamApplyMapper;
        this.userMapper = userMapper;
        this.wsHandler = wsHandler;
    }

    private void broadcastTeam(Long teamId, String type, Object payload) {
        try {
            Map<String, Object> msg = new HashMap<>();
            msg.put("type", type);
            // Always include teamId in payload for frontend routing
            if (payload instanceof Map) {
                ((Map) payload).put("teamId", teamId);
            }
            msg.put("payload", payload);
            wsHandler.broadcast(String.valueOf(teamId), objectMapper.writeValueAsString(msg));
        } catch (Exception ignored) {}
    }

    private Map<String, Object> _m(Object... kv) {
        Map<String, Object> m = new HashMap<>();
        for (int i = 0; i < kv.length; i += 2) {
            m.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return m;
    }

    private Integer getRole(Long teamId, Long userId) {
        TeamMember tm = teamMemberMapper.selectOne(new LambdaQueryWrapper<TeamMember>()
                .eq(TeamMember::getTeamId, teamId).eq(TeamMember::getUserId, userId));
        return tm != null ? tm.getRole() : null;
    }

    private boolean isMaster(Long teamId, Long userId) {
        Integer role = getRole(teamId, userId);
        return role != null && role == ROLE_MASTER;
    }

    private boolean isMember(Long teamId, Long userId) {
        return getRole(teamId, userId) != null;
    }

    // ========================================================
    // 1. 创建团队 — 团长 role=2, 邀请码=6位随机数
    // ========================================================
    @Transactional
    public Result<?> createTeam(String name, Long creatorId) {
        Team team = new Team();
        team.setName(name);
        team.setCreatorId(creatorId);
        team.setInviteCode(generateCode());
        teamMapper.insert(team);
        TeamMember member = new TeamMember();
        member.setTeamId(team.getId());
        member.setUserId(creatorId);
        member.setRole(ROLE_MASTER);
        member.setInviteCode(team.getInviteCode());
        teamMemberMapper.insert(member);
        broadcastTeam(team.getId(), "team:updated", _m("action", "created"));
        return Result.ok("团队创建成功", team);
    }

    // ========================================================
    // 2. 申请加入 — 写入 team_apply 待审核
    // ========================================================
    @Transactional
    public Result<?> applyToJoin(String inviteCode, Long userId) {
        Team team = teamMapper.selectOne(new LambdaQueryWrapper<Team>().eq(Team::getInviteCode, inviteCode));
        if (team == null) return Result.fail("邀请码无效");

        // Check already a member
        TeamMember exist = teamMemberMapper.selectOne(new LambdaQueryWrapper<TeamMember>()
                .eq(TeamMember::getTeamId, team.getId()).eq(TeamMember::getUserId, userId));
        if (exist != null) return Result.fail("你已经是团队成员");

        // Check already applied
        TeamApply existingApply = teamApplyMapper.selectOne(new LambdaQueryWrapper<TeamApply>()
                .eq(TeamApply::getTeamId, team.getId()).eq(TeamApply::getUid, userId)
                .eq(TeamApply::getStatus, 0));
        if (existingApply != null) return Result.fail("已提交申请，请等待团长审核");

        TeamApply apply = new TeamApply();
        apply.setTeamId(team.getId());
        apply.setUid(userId);
        apply.setStatus(0);
        teamApplyMapper.insert(apply);
        User applicant = userMapper.selectById(userId);
        String applicantName = applicant != null ? applicant.getNickname() : ("用户" + userId);
        broadcastTeam(team.getId(), "team:apply:submitted",
            _m("applyId", apply.getId(), "uid", userId, "userName", applicantName, "teamName", team.getName()));
        Map<String, Object> data = new HashMap<>();
        data.put("teamId", team.getId());
        data.put("teamName", team.getName());
        return Result.ok("申请已提交，等待团长审核", data);
    }

    // ========================================================
    // 3. 查看申请列表 (团长 only)
    // ========================================================
    public Result<?> getApplications(Long teamId, Long userId) {
        if (!isMaster(teamId, userId)) return Result.fail("只有团长可以查看申请列表");
        List<TeamApply> list = teamApplyMapper.selectList(new LambdaQueryWrapper<TeamApply>()
                .eq(TeamApply::getTeamId, teamId).eq(TeamApply::getStatus, 0));
        List<Map<String, Object>> result = new ArrayList<>();
        for (TeamApply a : list) {
            User user = userMapper.selectById(a.getUid());
            Map<String, Object> map = new HashMap<>();
            map.put("id", a.getId());
            map.put("teamId", a.getTeamId());
            map.put("uid", a.getUid());
            map.put("status", a.getStatus());
            map.put("createTime", a.getCreateTime());
            map.put("name", user != null ? user.getNickname() : "用户" + a.getUid());
            result.add(map);
        }
        return Result.ok(result);
    }

    // ========================================================
    // 4. 通过申请 → 插入 team_member (role=0 普通团员)
    // ========================================================
    @Transactional
    public Result<?> approveApplication(Long teamId, Long appId, Long operatorId) {
        if (!isMaster(teamId, operatorId)) return Result.fail("只有团长可以审核");
        TeamApply apply = teamApplyMapper.selectById(appId);
        if (apply == null || !apply.getTeamId().equals(teamId)) return Result.fail("申请不存在");
        if (apply.getStatus() != 0) return Result.fail("申请已处理");
        apply.setStatus(1);
        teamApplyMapper.updateById(apply);
        TeamMember member = new TeamMember();
        member.setTeamId(teamId);
        member.setUserId(apply.getUid());
        member.setRole(ROLE_MEMBER);
        teamMemberMapper.insert(member);
        User approvedUser = userMapper.selectById(apply.getUid());
        String approvedName = approvedUser != null ? approvedUser.getNickname() : ("用户" + apply.getUid());
        broadcastTeam(teamId, "team:member:joined", _m("userId", apply.getUid(), "userName", approvedName));
        broadcastTeam(teamId, "team:apply:approved", _m("uid", apply.getUid(), "userName", approvedName));
        return Result.ok("已通过");
    }

    // ========================================================
    // 5. 拒绝申请
    // ========================================================
    @Transactional
    public Result<?> rejectApplication(Long teamId, Long appId, Long operatorId) {
        if (!isMaster(teamId, operatorId)) return Result.fail("只有团长可以审核");
        TeamApply apply = teamApplyMapper.selectById(appId);
        if (apply == null || !apply.getTeamId().equals(teamId)) return Result.fail("申请不存在");
        apply.setStatus(2);
        teamApplyMapper.updateById(apply);
        User rejectedUser = userMapper.selectById(apply.getUid());
        String rejectedName = rejectedUser != null ? rejectedUser.getNickname() : ("用户" + apply.getUid());
        broadcastTeam(teamId, "team:apply:rejected", _m("uid", apply.getUid(), "userName", rejectedName));
        return Result.ok("已拒绝");
    }

    // ========================================================
    // 6. 获取团队成员（含用户名）
    // ========================================================
    public Result<?> getTeamMembers(Long teamId, Long userId) {
        if (!isMember(teamId, userId)) return Result.fail("无权查看该团队");
        List<TeamMember> members = teamMemberMapper.selectList(
                new LambdaQueryWrapper<TeamMember>().eq(TeamMember::getTeamId, teamId));
        List<Map<String, Object>> result = new ArrayList<>();
        for (TeamMember m : members) {
            User user = userMapper.selectById(m.getUserId());
            Map<String, Object> map = new HashMap<>();
            map.put("id", m.getId());
            map.put("teamId", m.getTeamId());
            map.put("userId", m.getUserId());
            map.put("role", m.getRole());
            map.put("joinedAt", m.getJoinedAt());
            map.put("name", user != null ? user.getNickname() : "用户" + m.getUserId());
            map.put("isActive", m.getDeleted() == 0);
            result.add(map);
        }
        return Result.ok(result);
    }

    // ========================================================
    // 7. 修改角色 (团长 only, 团队至少保留一个团长)
    // ========================================================
    public Result<?> changeRole(Long teamId, Long memberId, Integer newRole, Long operatorId) {
        if (!isMaster(teamId, operatorId)) return Result.fail("只有团长可以修改角色");
        if (newRole == null || newRole < 0 || newRole > 2) return Result.fail("无效的角色值");
        TeamMember member = teamMemberMapper.selectById(memberId);
        if (member == null || !member.getTeamId().equals(teamId)) return Result.fail("成员不存在");
        if (member.getUserId().equals(operatorId)) return Result.fail("不能修改自己的角色");

        // 如果要降级的是团长，检查是否是最后一个团长
        if (member.getRole() != null && member.getRole() == ROLE_MASTER && newRole != ROLE_MASTER) {
            int masterCount = countMasters(teamId);
            if (masterCount <= 1) return Result.fail("团队至少需要一名团长，不能降级");
        }

        member.setRole(newRole);
        teamMemberMapper.updateById(member);
        broadcastTeam(teamId, "team:member:role-changed", _m("memberId", memberId, "role", newRole));
        return Result.ok("角色已更新");
    }

    // ========================================================
    // 8. 移除成员 (团长 only, 团队至少保留一个团长)
    // ========================================================
    @Transactional
    public Result<?> removeMember(Long teamId, Long memberId, Long operatorId) {
        if (!isMaster(teamId, operatorId)) return Result.fail("只有团长可以移除成员");
        TeamMember member = teamMemberMapper.findByIdIgnoreDelete(memberId);
        if (member == null || !member.getTeamId().equals(teamId)) return Result.fail("成员不存在");
        if (member.getUserId().equals(operatorId)) return Result.fail("不能移除自己");

        // 如果要移除的是团长，检查是否是最后一个团长
        if (member.getRole() != null && member.getRole() == ROLE_MASTER) {
            int masterCount = countMasters(teamId);
            if (masterCount <= 1) return Result.fail("团队至少需要一名团长，不能移除最后一个团长");
        }

        teamMemberMapper.hardDelete(memberId);
        Team team = teamMapper.selectById(teamId);
        String teamName = team != null ? team.getName() : "";
        broadcastTeam(teamId, "team:member:removed", _m("memberId", memberId, "userId", member.getUserId(), "teamName", teamName));
        return Result.ok("成员已移除");
    }

    private int countMasters(Long teamId) {
        List<TeamMember> masters = teamMemberMapper.selectList(new LambdaQueryWrapper<TeamMember>()
                .eq(TeamMember::getTeamId, teamId).eq(TeamMember::getRole, ROLE_MASTER));
        return masters.size();
    }

    // ========================================================
    // 9. 我的团队列表
    // ========================================================
    public Result<?> getMyTeams(Long userId) {
        List<TeamMember> memberships = teamMemberMapper.selectList(
                new LambdaQueryWrapper<TeamMember>().eq(TeamMember::getUserId, userId));
        if (memberships.isEmpty()) return Result.ok(null);
        List<Long> teamIds = memberships.stream().map(TeamMember::getTeamId).collect(Collectors.toList());
        List<Team> teams = teamMapper.selectBatchIds(teamIds);
        return Result.ok(teams);
    }

    // ========================================================
    // 10. 重新生成邀请码 (团长 only)
    // ========================================================
    @Transactional
    public Result<?> generateNewInviteCode(Long teamId, Long userId) {
        if (!isMaster(teamId, userId)) return Result.fail("只有团长可以重新生成邀请码");
        Team team = teamMapper.selectById(teamId);
        team.setInviteCode(generateCode());
        teamMapper.updateById(team);
        broadcastTeam(teamId, "team:updated", _m("inviteCode", team.getInviteCode()));
        return Result.ok(team.getInviteCode());
    }

    // ========================================================
    // 11. 修改团队名称 (团长 only)
    // ========================================================
    public Result<?> updateTeamName(Long teamId, String name, Long userId) {
        if (!isMaster(teamId, userId)) return Result.fail("只有团长可以修改团队名称");
        Team team = teamMapper.selectById(teamId);
        team.setName(name);
        teamMapper.updateById(team);
        broadcastTeam(teamId, "team:updated", _m("name", name));
        return Result.ok("团队名称已更新");
    }

    // ========================================================
    // 12. 解散团队 (团长 only)
    // ========================================================
    @Transactional
    public Result<?> dissolveTeam(Long teamId, Long userId) {
        if (!isMaster(teamId, userId)) return Result.fail("只有团长可以解散团队");
        teamMapper.deleteById(teamId);
        broadcastTeam(teamId, "team:dissolved", _m("teamId", teamId));
        return Result.ok("团队已解散");
    }

    private String generateCode() {
        return String.format("%06d", new Random().nextInt(1000000));
    }
}
