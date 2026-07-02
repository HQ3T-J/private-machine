package com.standupsync.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.standupsync.dto.CreateStandupDTO;
import com.standupsync.dto.Result;
import com.standupsync.dto.SubmitSpeechDTO;
import com.standupsync.entity.*;
import com.standupsync.mapper.*;
import com.standupsync.websocket.StandupWebSocketHandler;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.regex.*;

@Service
public class StandupService {

    private final StandupMeetingMapper meetingMapper;
    private final StandupRecordMapper recordMapper;
    private final StandupActionItemMapper actionItemMapper;
    private final TeamMemberMapper teamMemberMapper;
    private final StandupWebSocketHandler wsHandler;
    private final AIService aiService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public StandupService(StandupMeetingMapper meetingMapper, StandupRecordMapper recordMapper,
                          StandupActionItemMapper actionItemMapper, TeamMemberMapper teamMemberMapper,
                          StandupWebSocketHandler wsHandler, AIService aiService) {
        this.meetingMapper = meetingMapper;
        this.recordMapper = recordMapper;
        this.actionItemMapper = actionItemMapper;
        this.teamMemberMapper = teamMemberMapper;
        this.wsHandler = wsHandler;
        this.aiService = aiService;
    }

    private boolean isTeamMember(Long teamId, Long userId) {
        TeamMember tm = teamMemberMapper.selectOne(new LambdaQueryWrapper<TeamMember>()
                .eq(TeamMember::getTeamId, teamId).eq(TeamMember::getUserId, userId));
        return tm != null;
    }

    public Result<?> getStandupList(Long teamId, Long userId) {
        if (!isTeamMember(teamId, userId)) return Result.fail("无权查看该团队站会");
        List<StandupMeeting> list = meetingMapper.selectList(
                new LambdaQueryWrapper<StandupMeeting>().eq(StandupMeeting::getTeamId, teamId)
                        .orderByDesc(StandupMeeting::getMeetingDate));
        return Result.ok(list);
    }

    @Transactional
    public Result<?> createStandup(CreateStandupDTO dto, Long createdBy) {
        StandupMeeting meeting = new StandupMeeting();
        meeting.setTeamId(dto.getTeamId());
        meeting.setSprint(dto.getSprint());
        meeting.setMeetingDate(LocalDate.now());
        meeting.setMode(dto.getMode() != null ? dto.getMode() : "live");
        meeting.setStatus("created");
        meeting.setCountdownSeconds(900);
        meeting.setCreatedBy(createdBy);
        meetingMapper.insert(meeting);

        // Broadcast to team room so all members see the new standup
        try {
            Map<String, Object> msg = new HashMap<>();
            msg.put("type", "standup:created");
            Map<String, Object> payload = new HashMap<>();
            payload.put("id", meeting.getId());
            payload.put("teamId", meeting.getTeamId());
            payload.put("sprint", meeting.getSprint());
            payload.put("mode", meeting.getMode());
            payload.put("meetingDate", meeting.getMeetingDate().toString());
            msg.put("payload", payload);
            wsHandler.broadcast(String.valueOf(meeting.getTeamId()), objectMapper.writeValueAsString(msg));
        } catch (Exception ignored) {}

        // Create records for each member
        for (int i = 0; i < dto.getMemberIds().size(); i++) {
            StandupRecord record = new StandupRecord();
            record.setStandupId(meeting.getId());
            record.setUserId(dto.getMemberIds().get(i));
            record.setSpeakOrder(i);
            record.setSpeakStatus("waiting");
            recordMapper.insert(record);
        }
        return Result.ok("站会创建成功", meeting);
    }

    @Transactional
    public Result<?> startStandup(Long standupId, Long userId) {
        StandupMeeting meeting = meetingMapper.selectById(standupId);
        if (meeting == null) return Result.fail("站会不存在");
        // Only Scrum Master or Tech Lead can start
        TeamMember tm = teamMemberMapper.selectOne(new LambdaQueryWrapper<TeamMember>()
                .eq(TeamMember::getTeamId, meeting.getTeamId()).eq(TeamMember::getUserId, userId));
        if (tm == null || (tm.getRole() == null || tm.getRole() == 0))
            return Result.fail("只有团长或管理员可以开启站会");

        meeting.setStatus("active");
        meeting.setCountdownEndAt(LocalDateTime.now().plusSeconds(900));
        meetingMapper.updateById(meeting);

        // Broadcast via WebSocket
        try {
            Map<String, Object> msg = new HashMap<>();
            msg.put("type", "standup:state:sync");
            Map<String, Object> payload = new HashMap<>();
            payload.put("status", "active");
            payload.put("countdownSeconds", 900);
            msg.put("payload", payload);
            wsHandler.broadcast(String.valueOf(standupId), objectMapper.writeValueAsString(msg));
        } catch (Exception ignored) {}
        return Result.ok("站会已开始");
    }

    @Transactional
    public Result<?> submitSpeech(Long standupId, Long userId, SubmitSpeechDTO dto) {
        StandupRecord record = recordMapper.selectOne(new LambdaQueryWrapper<StandupRecord>()
                .eq(StandupRecord::getStandupId, standupId).eq(StandupRecord::getUserId, userId));
        if (record == null) return Result.fail("发言记录不存在");
        record.setYesterdayWork(dto.getYesterdayWork());
        record.setTodayPlan(dto.getTodayPlan());
        record.setBlockers(dto.getBlockers());
        record.setSpeakStatus("done");
        record.setSubmittedAt(LocalDateTime.now());
        recordMapper.updateById(record);

        // Broadcast to all members
        try {
            Map<String, Object> msg = new HashMap<>();
            msg.put("type", "standup:speech:submitted");
            Map<String, Object> payload = new HashMap<>();
            payload.put("speakerId", String.valueOf(userId));
            payload.put("yesterday", dto.getYesterdayWork());
            payload.put("today", dto.getTodayPlan());
            payload.put("blockers", dto.getBlockers());
            msg.put("payload", payload);
            wsHandler.broadcast(String.valueOf(standupId), objectMapper.writeValueAsString(msg));
        } catch (Exception ignored) {}
        return Result.ok("发言已提交");
    }

    public Result<?> getStandupDetail(Long standupId, Long userId) {
        StandupMeeting meeting = meetingMapper.selectById(standupId);
        if (meeting == null) return Result.fail("站会不存在");
        if (!isTeamMember(meeting.getTeamId(), userId)) return Result.fail("无权查看");
        List<StandupRecord> records = recordMapper.selectList(
                new LambdaQueryWrapper<StandupRecord>().eq(StandupRecord::getStandupId, standupId)
                        .orderByAsc(StandupRecord::getSpeakOrder));
        Map<String, Object> result = new HashMap<>();
        result.put("meeting", meeting);
        result.put("records", records);
        return Result.ok(result);
    }

    @Transactional
    public Result<?> endStandup(Long standupId, Long userId) {
        StandupMeeting meeting = meetingMapper.selectById(standupId);
        if (meeting == null) return Result.fail("站会不存在");
        meeting.setStatus("archived");
        meeting.setIsArchived(1);
        meeting.setArchivedAt(LocalDateTime.now());
        meetingMapper.updateById(meeting);

        try {
            Map<String, Object> msg = new HashMap<>();
            msg.put("type", "standup:ended");
            Map<String, Object> payload = new HashMap<>();
            payload.put("standupId", standupId);
            msg.put("payload", payload);
            // Notify meeting room
            wsHandler.broadcast(String.valueOf(standupId), objectMapper.writeValueAsString(msg));
            // Also notify team room so list views update
            Map<String, Object> teamMsg = new HashMap<>();
            teamMsg.put("type", "standup:list-changed");
            Map<String, Object> listPayload = new HashMap<>();
            listPayload.put("standupId", standupId);
            listPayload.put("action", "ended");
            teamMsg.put("payload", listPayload);
            wsHandler.broadcast(String.valueOf(meeting.getTeamId()), objectMapper.writeValueAsString(teamMsg));
        } catch (Exception ignored) {}
        return Result.ok("站会已归档");
    }

    public Result<?> pasteChatLog(Long standupId, String text, Long userId) {
        StandupMeeting meeting = meetingMapper.selectById(standupId);
        if (meeting == null) return Result.fail("站会不存在");
        if (!isTeamMember(meeting.getTeamId(), userId)) return Result.fail("无权操作");
        List<Map<String, String>> parsed = parseChatLog(text);
        int count = 0;
        for (Map<String, String> entry : parsed) {
            String name = entry.get("name");
            String content = entry.get("content");
            // Find record by matching user name (via member table)
            List<TeamMember> members = teamMemberMapper.selectList(new LambdaQueryWrapper<TeamMember>()
                    .eq(TeamMember::getTeamId, meetingMapper.selectById(standupId).getTeamId()));
            // We'd need UserMapper too. Simplified: just store as generic.
            if (!content.isEmpty()) {
                StandupRecord record = recordMapper.selectOne(new LambdaQueryWrapper<StandupRecord>()
                        .eq(StandupRecord::getStandupId, standupId).eq(StandupRecord::getSpeakOrder, count));
                if (record != null) {
                    record.setYesterdayWork(name + ": " + content);
                    record.setSpeakStatus("done");
                    record.setSubmittedAt(LocalDateTime.now());
                    recordMapper.updateById(record);
                    count++;
                }
            }
        }
        return Result.ok("已解析 " + count + " 条发言");
    }

    @Transactional
    public Result<?> generateAISummary(Long standupId, Long userId) {
        StandupMeeting meeting = meetingMapper.selectById(standupId);
        if (meeting == null) return Result.fail("站会不存在");
        if (!isTeamMember(meeting.getTeamId(), userId)) return Result.fail("无权操作");
        List<StandupRecord> records = recordMapper.selectList(
                new LambdaQueryWrapper<StandupRecord>().eq(StandupRecord::getStandupId, standupId));
        if (records.isEmpty()) return Result.fail("没有发言记录");

        // Delete old action items
        actionItemMapper.delete(new LambdaQueryWrapper<StandupActionItem>()
                .eq(StandupActionItem::getStandupId, standupId));

        try {
            // Try AI summary (falls back to local heuristic if API unavailable)
            Map<String, Object> aiResult = aiService.summarize(standupId, records);

            // Save action items from AI
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> items = (List<Map<String, Object>>) aiResult.get("actionItems");
            if (items != null) {
                for (int i = 0; i < items.size(); i++) {
                    StandupActionItem item = new StandupActionItem();
                    item.setStandupId(standupId);
                    item.setContent((String) items.get(i).get("content"));
                    item.setAssigneeId(Long.valueOf(String.valueOf(items.get(i).getOrDefault("assigneeId", "1"))));
                    item.setPriority((String) items.get(i).getOrDefault("priority", "medium"));
                    item.setSortOrder(i);
                    actionItemMapper.insert(item);
                }
            }
            return Result.ok("AI整理完成", aiResult);
        } catch (Exception e) {
            return Result.ok("AI服务异常，展示原始记录", buildFallbackSummary(records));
        }
    }

    public Result<?> getSummary(Long standupId, Long userId) {
        StandupMeeting meeting = meetingMapper.selectById(standupId);
        if (meeting == null) return Result.fail("站会不存在");
        if (!isTeamMember(meeting.getTeamId(), userId)) return Result.fail("无权查看");
        List<StandupRecord> records = recordMapper.selectList(
                new LambdaQueryWrapper<StandupRecord>().eq(StandupRecord::getStandupId, standupId));
        List<StandupActionItem> items = actionItemMapper.selectList(
                new LambdaQueryWrapper<StandupActionItem>().eq(StandupActionItem::getStandupId, standupId));

        Map<String, Object> summary = buildFallbackSummary(records);
        summary.put("actionItems", items);
        summary.put("standupId", standupId);
        summary.put("isArchived", meeting.getIsArchived());
        return Result.ok(summary);
    }

    public Result<?> classifyText(String text, Long userId) {
        // Local keyword classification (instant, no AI API call)
        Map<String, Object> result = new HashMap<>();
        String t = text.toLowerCase();

        int yesterdayScore = 0, todayScore = 0, blockerScore = 0;

        if (t.contains("昨天") || t.contains("完成") || t.contains("做完了") || t.contains("了")) yesterdayScore += 10;
        if (t.contains("今天") || t.contains("计划") || t.contains("要做") || t.contains("打算")) todayScore += 10;
        if (t.contains("阻碍") || t.contains("问题") || t.contains("卡住") || t.contains("需要帮助")) blockerScore += 10;

        // Default to today for Chinese sentences ending with 要/会/想
        if (t.endsWith("要做") || t.endsWith("要") || t.endsWith("打算")) todayScore += 5;
        if (t.contains("已完成") || t.contains("做完了") || t.contains("搞定了")) yesterdayScore += 15;

        String category;
        double confidence;
        int maxScore = Math.max(yesterdayScore, Math.max(todayScore, blockerScore));
        if (maxScore == 0) { category = "today"; confidence = 0.5; }
        else if (maxScore == yesterdayScore) { category = "yesterday"; confidence = Math.min(0.9, yesterdayScore / 20.0); }
        else if (maxScore == blockerScore) { category = "blocker"; confidence = Math.min(0.9, blockerScore / 20.0); }
        else { category = "today"; confidence = Math.min(0.9, todayScore / 20.0); }

        result.put("category", category);
        result.put("confidence", confidence);
        return Result.ok(result);
    }

    public Result<?> updateActionItem(Long itemId, String content, String priority, Long assigneeId, Long userId) {
        StandupActionItem item = actionItemMapper.selectById(itemId);
        if (item == null) return Result.fail("ActionItem不存在");
        if (content != null) item.setContent(content);
        if (priority != null) item.setPriority(priority);
        if (assigneeId != null) item.setAssigneeId(assigneeId);
        actionItemMapper.updateById(item);
        return Result.ok("已更新");
    }

    private List<Map<String, String>> parseChatLog(String text) {
        List<Map<String, String>> results = new ArrayList<>();
        if (text == null || text.trim().isEmpty()) return results;
        for (String line : text.split("\n")) {
            line = line.trim();
            if (line.isEmpty()) continue;
            Matcher m = Pattern.compile("^(.+?)[：:](.+)").matcher(line);
            if (m.find()) {
                Map<String, String> entry = new HashMap<>();
                entry.put("name", m.group(1).trim());
                entry.put("content", m.group(2).trim());
                results.add(entry);
            }
        }
        return results;
    }

    private Map<String, Object> buildFallbackSummary(List<StandupRecord> records) {
        List<String> doneList = new ArrayList<>();
        List<String> planList = new ArrayList<>();
        List<String> blockers = new ArrayList<>();
        for (StandupRecord r : records) {
            if (r.getYesterdayWork() != null && !r.getYesterdayWork().trim().isEmpty())
                doneList.add("用户" + r.getUserId() + ": " + r.getYesterdayWork());
            if (r.getTodayPlan() != null && !r.getTodayPlan().trim().isEmpty())
                planList.add("用户" + r.getUserId() + ": " + r.getTodayPlan());
            if (r.getBlockers() != null && !r.getBlockers().trim().isEmpty())
                blockers.add("用户" + r.getUserId() + ": " + r.getBlockers());
        }
        Map<String, Object> result = new HashMap<>();
        result.put("doneList", doneList);
        result.put("planList", planList);
        result.put("blockers", blockers);
        return result;
    }
}
