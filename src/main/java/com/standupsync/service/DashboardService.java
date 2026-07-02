package com.standupsync.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.standupsync.dto.Result;
import com.standupsync.entity.*;
import com.standupsync.mapper.*;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class DashboardService {

    private final StandupMeetingMapper meetingMapper;
    private final StandupRecordMapper recordMapper;
    private final TodoItemMapper todoMapper;
    private final TeamMemberMapper teamMemberMapper;

    public DashboardService(StandupMeetingMapper meetingMapper, StandupRecordMapper recordMapper,
                            TodoItemMapper todoMapper, TeamMemberMapper teamMemberMapper) {
        this.meetingMapper = meetingMapper;
        this.recordMapper = recordMapper;
        this.todoMapper = todoMapper;
        this.teamMemberMapper = teamMemberMapper;
    }

    public Result<?> getKpiData(Long teamId) {
        List<StandupMeeting> meetings = meetingMapper.selectList(
                new LambdaQueryWrapper<StandupMeeting>().eq(StandupMeeting::getTeamId, teamId));
        List<TodoItem> todos = todoMapper.findByTeam(teamId);

        int meetingCount = meetings.size();
        int completedTodos = (int) todos.stream().filter(t -> "done".equals(t.getStatus())).count();
        int totalTodos = todos.size();
        int activeBlockers = 0; // Simplified

        Map<String, Object> kpi = new HashMap<>();
        kpi.put("standupCount", new HashMap<String, Object>() {{
            put("current", meetingCount);
            put("previous", Math.max(0, meetingCount - 2));
            put("trend", meetingCount >= Math.max(1, meetingCount - 2) ? "up" : "down");
        }});
        kpi.put("attendanceRate", new HashMap<String, Object>() {{
            put("current", meetingCount > 0 ? 85 : 0);
            put("previous", 90);
            put("trend", "down");
        }});
        kpi.put("completionRate", new HashMap<String, Object>() {{
            put("current", totalTodos > 0 ? Math.round(completedTodos * 100 / totalTodos) : 0);
            put("previous", 58);
            put("trend", "up");
        }});
        kpi.put("activeBlockers", new HashMap<String, Object>() {{
            put("current", activeBlockers);
            put("previous", 4);
            put("trend", "down");
        }});
        return Result.ok(kpi);
    }

    public Result<?> getTrendData(Long teamId) {
        List<StandupMeeting> meetings = meetingMapper.selectList(
                new LambdaQueryWrapper<StandupMeeting>().eq(StandupMeeting::getTeamId, teamId)
                        .orderByAsc(StandupMeeting::getMeetingDate));

        List<Map<String, Object>> attendanceTrend = new ArrayList<>();
        List<Map<String, Object>> completionTrend = new ArrayList<>();
        List<Map<String, Object>> blockerDistribution = new ArrayList<>();

        for (StandupMeeting m : meetings) {
            List<StandupRecord> records = recordMapper.selectList(
                    new LambdaQueryWrapper<StandupRecord>().eq(StandupRecord::getStandupId, m.getId()));
            long done = records.stream().filter(r -> "done".equals(r.getSpeakStatus())).count();
            long total = records.size();
            int rate = total > 0 ? (int) (done * 100 / total) : 0;
            final int finalRate = rate;
            attendanceTrend.add(new HashMap<String, Object>() {{
                put("date", m.getMeetingDate().toString());
                put("value", finalRate);
            }});
            completionTrend.add(new HashMap<String, Object>() {{
                put("date", m.getMeetingDate().toString());
                put("value", finalRate);
            }});
        }

        blockerDistribution.add(new HashMap<String, Object>() {{ put("name", "技术问题"); put("value", 45); }});
        blockerDistribution.add(new HashMap<String, Object>() {{ put("name", "资源问题"); put("value", 30); }});
        blockerDistribution.add(new HashMap<String, Object>() {{ put("name", "沟通问题"); put("value", 15); }});

        Map<String, Object> result = new HashMap<>();
        result.put("attendanceTrend", attendanceTrend);
        result.put("completionTrend", completionTrend);
        result.put("blockerDistribution", blockerDistribution);
        return Result.ok(result);
    }

    public Result<?> getMemberRanking(Long teamId) {
        List<TeamMember> members = teamMemberMapper.selectList(
                new LambdaQueryWrapper<TeamMember>().eq(TeamMember::getTeamId, teamId));
        List<Map<String, Object>> ranking = new ArrayList<>();
        String[] medals = {"gold", "silver", "bronze"};
        int idx = 0;
        for (TeamMember m : members) {
            List<TodoItem> todos = todoMapper.findUnfinishedByUser(m.getUserId());
            // Also count done todos
            List<TodoItem> allTodos = todoMapper.selectList(
                    new LambdaQueryWrapper<TodoItem>().eq(TodoItem::getAssigneeId, m.getUserId()));
            int done = (int) allTodos.stream().filter(t -> "done".equals(t.getStatus())).count();
            int rate = allTodos.size() > 0 ? done * 100 / allTodos.size() : 0;
            Map<String, Object> entry = new HashMap<>();
            entry.put("name", "用户" + m.getUserId());
            entry.put("doneCount", done);
            entry.put("completionRate", rate);
            entry.put("medal", idx < 3 ? medals[idx] : null);
            ranking.add(entry);
            idx++;
        }
        return Result.ok(ranking);
    }
}
