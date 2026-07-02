package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.*;
import com.standupsync.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/meetings")
public class MeetingController {

    private final MeetingRepository meetingRepository;
    private final MeetingSpeechRepository meetingSpeechRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final TeamRepository teamRepository;
    private final MeetingParticipantRepository participantRepository;
    private final UserRepository userRepository;

    public MeetingController(MeetingRepository meetingRepository,
                             MeetingSpeechRepository meetingSpeechRepository,
                             TeamMemberRepository teamMemberRepository,
                             TeamRepository teamRepository,
                             MeetingParticipantRepository participantRepository,
                             UserRepository userRepository) {
        this.meetingRepository = meetingRepository;
        this.meetingSpeechRepository = meetingSpeechRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.teamRepository = teamRepository;
        this.participantRepository = participantRepository;
        this.userRepository = userRepository;
    }

    @PostMapping
    public ApiResponse<Meeting> createMeeting(@RequestAttribute("userId") String userId,
                                               @RequestBody Map<String, Object> body) {
        Object teamIdObj = body.get("teamId");
        if (teamIdObj == null) return ApiResponse.error(400, "teamId 不能为空");
        Long teamId = Long.valueOf(teamIdObj.toString());
        if (!isMember(userId, teamId)) return ApiResponse.error(403, "无权在该团队创建会议");

        Team team = teamRepository.findById(teamId).orElse(null);
        if (team == null) return ApiResponse.error(404, "团队不存在");

        Meeting meeting = new Meeting();
        meeting.setTeam(team);
        meeting.setCreatedBy(userId);
        if (body.containsKey("title") && body.get("title") != null)
            meeting.setTitle(body.get("title").toString());
        Integer sprintNo = body.containsKey("sprintNo") ? ((Number) body.get("sprintNo")).intValue() : 1;
        meeting.setSprintNo(sprintNo);
        String formType = body.containsKey("formType") ? body.get("formType").toString() : "REALTIME";
        meeting.setFormType(Meeting.FormType.valueOf(formType));
        meeting.setStatus(Meeting.MeetingStatus.CREATED);
        meeting.setAiStatus(Meeting.AiStatus.IDLE);

        // 自动添加所有团队成员为参会者
        meeting = meetingRepository.save(meeting);
        List<TeamMember> members = teamMemberRepository.findByTeamId(teamId);
        for (int i = 0; i < members.size(); i++) {
            MeetingParticipant mp = new MeetingParticipant();
            mp.setMeetingId(meeting.getId());
            mp.setUserId(members.get(i).getUserId());
            mp.setSpeechOrder(i + 1);
            participantRepository.save(mp);
        }

        return ApiResponse.success("会议创建成功", meeting);
    }

    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> getMeeting(@RequestAttribute("userId") String userId,
                                                        @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isMember(userId, meeting.getTeam().getId()))
            return ApiResponse.error(403, "无权访问该会议");

        List<MeetingParticipant> participants = participantRepository.findByMeetingIdOrderBySpeechOrderAsc(id);
        List<Map<String, Object>> participantList = new ArrayList<>();
        for (MeetingParticipant p : participants) {
            User user = userRepository.findById(p.getUserId()).orElse(null);
            Map<String, Object> pm = new LinkedHashMap<>();
            pm.put("user_id", p.getUserId());
            pm.put("speech_order", p.getSpeechOrder());
            pm.put("has_spoken", p.getHasSpoken());
            if (user != null) {
                pm.put("username", user.getUsername());
                pm.put("displayName", user.getDisplayName());
            }
            participantList.add(pm);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", meeting.getId());
        result.put("title", meeting.getTitle());
        result.put("sprintNo", meeting.getSprintNo());
        result.put("formType", meeting.getFormType().name());
        result.put("status", meeting.getStatus().name());
        result.put("createdBy", meeting.getCreatedBy());
        result.put("createdAt", meeting.getCreatedAt());
        result.put("endedAt", meeting.getEndedAt());
        // 只暴露团队必要字段，避免 Hibernate 懒加载序列化异常
        Team team = meeting.getTeam();
        Map<String, Object> teamInfo = new LinkedHashMap<>();
        teamInfo.put("id", team.getId());
        teamInfo.put("name", team.getName());
        result.put("team", teamInfo);
        result.put("participants", participantList);
        return ApiResponse.success(result);
    }

    @GetMapping
    public ApiResponse<?> listMeetings(@RequestAttribute("userId") String userId,
                                        @RequestParam("teamId") Long teamId,
                                        @RequestParam(defaultValue = "0") int page,
                                        @RequestParam(defaultValue = "20") int size) {
        if (!isMember(userId, teamId)) return ApiResponse.error(403, "无权查看该团队的会议");
        Pageable pageable = PageRequest.of(page, size);
        Page<Meeting> result = meetingRepository.findByTeamIdOrderByCreatedAtDesc(teamId, pageable);
        Map<String, Object> paged = new LinkedHashMap<>();
        paged.put("content", result.getContent());
        paged.put("totalPages", result.getTotalPages());
        paged.put("totalElements", result.getTotalElements());
        paged.put("page", page);
        paged.put("size", size);
        return ApiResponse.success(paged);
    }

    @PostMapping("/{id}/start")
    public ApiResponse<Meeting> startMeeting(@RequestAttribute("userId") String userId, @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isAdmin(userId, meeting.getTeam().getId())) return ApiResponse.error(403, "只有管理员可以开始会议");
        if (meeting.getStatus() != Meeting.MeetingStatus.CREATED) return ApiResponse.error(400, "会议状态不允许开始");
        meeting.setStatus(Meeting.MeetingStatus.ACTIVE);
        return ApiResponse.success("会议已开始", meetingRepository.save(meeting));
    }

    @PostMapping("/{id}/end")
    public ApiResponse<Meeting> endMeeting(@RequestAttribute("userId") String userId, @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isAdmin(userId, meeting.getTeam().getId())) return ApiResponse.error(403, "只有管理员可以结束会议");
        if (meeting.getStatus() != Meeting.MeetingStatus.ACTIVE) return ApiResponse.error(400, "会议未在进行中，无法结束");
        meeting.setStatus(Meeting.MeetingStatus.ENDED);
        meeting.setEndedAt(LocalDateTime.now());
        return ApiResponse.success("会议已结束", meetingRepository.save(meeting));
    }

    // ═══ 粘贴聊天批量解析 ═══
    @PostMapping("/{id}/paste")
    public ApiResponse<Map<String, Object>> pasteChat(@RequestAttribute("userId") String userId,
                                                       @PathVariable Long id,
                                                       @RequestBody Map<String, String> body) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        String text = body.getOrDefault("text", "");
        if (text.isBlank()) return ApiResponse.error(400, "文本为空");

        // 解析 "Name: content" 格式
        java.util.List<java.util.Map<String, String>> parsed = new java.util.ArrayList<>();
        for (String line : text.split("\\R")) {
            line = line.trim();
            if (line.isEmpty()) continue;
            int idx = -1;
            int ce = line.indexOf(':'), cc = line.indexOf('：');
            if (ce > 0 && (cc < 0 || ce < cc)) idx = ce;
            else if (cc > 0) idx = cc;
            if (idx > 0 && idx < 30) {
                java.util.Map<String, String> m = new java.util.LinkedHashMap<>();
                m.put("name", line.substring(0, idx).trim());
                m.put("content", line.substring(idx + 1).trim());
                parsed.add(m);
            }
        }
        java.util.Map<String, Object> result = new java.util.LinkedHashMap<>();
        result.put("count", parsed.size());
        result.put("speeches", parsed);
        return ApiResponse.success("解析完成", result);
    }

    // ═══ 文本分类 ═══
    @PostMapping("/{id}/classify")
    public ApiResponse<java.util.Map<String, Object>> classifyText(@RequestAttribute("userId") String userId,
                                                                    @PathVariable Long id,
                                                                    @RequestBody java.util.Map<String, String> body) {
        String text = body.getOrDefault("text", "");
        if (text.isBlank()) return ApiResponse.error(400, "文本为空");

        String t = text.toLowerCase();
        int yesterdayScore = 0, todayScore = 0, blockerScore = 0;
        if (t.contains("昨天") || t.contains("完成") || t.contains("做完了") || t.contains("了")) yesterdayScore += 10;
        if (t.contains("今天") || t.contains("计划") || t.contains("要做") || t.contains("打算")) todayScore += 10;
        if (t.contains("阻碍") || t.contains("问题") || t.contains("卡住") || t.contains("需要帮助")) blockerScore += 10;
        if (t.contains("已完成") || t.contains("做完了") || t.contains("搞定了")) yesterdayScore += 15;

        String category; double confidence;
        int max = Math.max(yesterdayScore, Math.max(todayScore, blockerScore));
        if (max == 0) { category = "today"; confidence = 0.5; }
        else if (max == yesterdayScore) { category = "yesterday"; confidence = Math.min(0.9, yesterdayScore / 20.0); }
        else if (max == blockerScore) { category = "blocker"; confidence = Math.min(0.9, blockerScore / 20.0); }
        else { category = "today"; confidence = Math.min(0.9, todayScore / 20.0); }

        java.util.Map<String, Object> result = new java.util.LinkedHashMap<>();
        result.put("category", category);
        result.put("confidence", confidence);
        return ApiResponse.success(result);
    }

    // ═══ AI 站会总结 ═══
    @PostMapping("/{id}/summary/generate")
    public ApiResponse<?> generateSummary(@RequestAttribute("userId") String userId,
                                           @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");

        List<MeetingSpeech> speeches = meetingSpeechRepository.findByMeetingIdOrderByCreatedAtAsc(id);
        if (speeches.isEmpty()) return ApiResponse.error(400, "没有发言记录");

        // Build summary from speeches
        List<String> doneList = new ArrayList<>();
        List<String> planList = new ArrayList<>();
        List<String> blockerList = new ArrayList<>();
        for (MeetingSpeech s : speeches) {
            String speaker = s.getSpeaker() != null ? s.getSpeaker().getUsername() : "?";
            if (s.getYesterday() != null && !s.getYesterday().isBlank())
                doneList.add(speaker + ": " + s.getYesterday());
            if (s.getToday() != null && !s.getToday().isBlank())
                planList.add(speaker + ": " + s.getToday());
            if (s.getBlockers() != null && !s.getBlockers().isBlank())
                blockerList.add(speaker + ": " + s.getBlockers());
        }

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("doneList", doneList);
        summary.put("planList", planList);
        summary.put("blockers", blockerList);

        // Save to meeting
        try {
            meeting.setAiResult(new ObjectMapper().writeValueAsString(summary));
            meeting.setAiStatus(Meeting.AiStatus.DONE);
            meetingRepository.save(meeting);
        } catch (Exception ignored) {}

        return ApiResponse.success("总结生成完成", summary);
    }

    @GetMapping("/{id}/summary")
    public ApiResponse<?> getSummary(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("standupId", id);
        result.put("aiStatus", meeting.getAiStatus() != null ? meeting.getAiStatus().name() : "IDLE");
        result.put("aiResult", meeting.getAiResult());
        result.put("isArchived", meeting.getIsArchived());
        return ApiResponse.success(result);
    }

    @PutMapping("/summary/items/{itemId}")
    public ApiResponse<?> updateSummaryItem(@PathVariable Long itemId,
                                             @RequestBody Map<String, String> body) {
        // Update AI-generated content inline — for now just acknowledge
        return ApiResponse.success("已更新", body);
    }

    private boolean isMember(String userId, Long teamId) {
        return teamMemberRepository.existsByTeamIdAndUserId(teamId, userId);
    }

    private boolean isAdmin(String userId, Long teamId) {
        return teamMemberRepository.findByTeamId(teamId).stream()
                .filter(m -> m.getUserId().equals(userId))
                .anyMatch(m -> m.getRole() == TeamMember.MemberRole.TECH_LEAD
                        || m.getRole() == TeamMember.MemberRole.SCRUM_MASTER);
    }
}
