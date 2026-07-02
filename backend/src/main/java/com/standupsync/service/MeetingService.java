package com.standupsync.service;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.*;
import com.standupsync.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class MeetingService {

    private static final Logger log = LoggerFactory.getLogger(MeetingService.class);

    private final MeetingRepository meetingRepository;
    private final MeetingSpeechRepository speechRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final TeamRepository teamRepository;
    private final MeetingParticipantRepository participantRepository;
    private final UserRepository userRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public MeetingService(MeetingRepository meetingRepository,
                          MeetingSpeechRepository speechRepository,
                          TeamMemberRepository teamMemberRepository,
                          TeamRepository teamRepository,
                          MeetingParticipantRepository participantRepository,
                          UserRepository userRepository) {
        this.meetingRepository = meetingRepository;
        this.speechRepository = speechRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.teamRepository = teamRepository;
        this.participantRepository = participantRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public ApiResponse<Meeting> createMeeting(String userId, Map<String, Object> body) {
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

        meeting = meetingRepository.save(meeting);
        autoAddParticipants(meeting, teamId);
        return ApiResponse.success("会议创建成功", meeting);
    }

    public ApiResponse<Map<String, Object>> getMeeting(String userId, Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isMember(userId, meeting.getTeam().getId()))
            return ApiResponse.error(403, "无权访问该会议");

        List<MeetingParticipant> participants = participantRepository.findByMeetingIdOrderBySpeechOrderAsc(id);
        List<Map<String, Object>> participantList = buildParticipantList(participants);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", meeting.getId());
        result.put("title", meeting.getTitle());
        result.put("sprintNo", meeting.getSprintNo());
        result.put("status", meeting.getStatus().name());
        result.put("createdBy", meeting.getCreatedBy());
        result.put("createdAt", meeting.getCreatedAt());
        result.put("endedAt", meeting.getEndedAt());

        Team team = meeting.getTeam();
        Map<String, Object> teamInfo = new LinkedHashMap<>();
        teamInfo.put("id", team.getId());
        teamInfo.put("name", team.getName());
        result.put("team", teamInfo);
        result.put("participants", participantList);
        return ApiResponse.success(result);
    }

    public ApiResponse<?> listMeetings(String userId, Long teamId, int page, int size) {
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

    public ApiResponse<Meeting> startMeeting(String userId, Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isAdmin(userId, meeting.getTeam().getId())) return ApiResponse.error(403, "只有管理员可以开始会议");
        if (meeting.getStatus() != Meeting.MeetingStatus.CREATED) return ApiResponse.error(400, "会议状态不允许开始");
        meeting.setStatus(Meeting.MeetingStatus.ACTIVE);
        return ApiResponse.success("会议已开始", meetingRepository.save(meeting));
    }

    public ApiResponse<Meeting> endMeeting(String userId, Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isAdmin(userId, meeting.getTeam().getId())) return ApiResponse.error(403, "只有管理员可以结束会议");
        if (meeting.getStatus() != Meeting.MeetingStatus.ACTIVE) return ApiResponse.error(400, "会议未在进行中");
        meeting.setStatus(Meeting.MeetingStatus.ENDED);
        meeting.setEndedAt(LocalDateTime.now());
        return ApiResponse.success("会议已结束", meetingRepository.save(meeting));
    }

    public ApiResponse<Map<String, Object>> pasteChat(Long meetingId, String text) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (text == null || text.isBlank()) return ApiResponse.error(400, "文本为空");

        List<Map<String, String>> parsed = new ArrayList<>();
        for (String line : text.split("\\R")) {
            line = line.trim();
            if (line.isEmpty()) continue;
            int ce = line.indexOf(':'), cc = line.indexOf('：');
            int idx = (ce > 0 && (cc < 0 || ce < cc)) ? ce : cc;
            if (idx > 0 && idx < 30) {
                Map<String, String> m = new LinkedHashMap<>();
                m.put("name", line.substring(0, idx).trim());
                m.put("content", line.substring(idx + 1).trim());
                parsed.add(m);
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("count", parsed.size());
        result.put("speeches", parsed);
        return ApiResponse.success("解析完成", result);
    }

    public ApiResponse<Map<String, Object>> generateSummary(String userId, Long meetingId) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");

        List<MeetingSpeech> speeches = speechRepository.findByMeetingIdOrderByCreatedAtAsc(meetingId);
        if (speeches.isEmpty()) return ApiResponse.error(400, "没有发言记录");

        List<String> doneList = new ArrayList<>(), planList = new ArrayList<>(), blockerList = new ArrayList<>();
        for (MeetingSpeech s : speeches) {
            String speaker = s.getSpeaker() != null ? s.getSpeaker().getUsername() : "?";
            if (s.getYesterday() != null && !s.getYesterday().isBlank()) doneList.add(speaker + ": " + s.getYesterday());
            if (s.getToday() != null && !s.getToday().isBlank()) planList.add(speaker + ": " + s.getToday());
            if (s.getBlockers() != null && !s.getBlockers().isBlank()) blockerList.add(speaker + ": " + s.getBlockers());
        }

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("doneList", doneList);
        summary.put("planList", planList);
        summary.put("blockers", blockerList);

        try {
            meeting.setAiResult(objectMapper.writeValueAsString(summary));
            meeting.setAiStatus(Meeting.AiStatus.DONE);
            meetingRepository.save(meeting);
        } catch (Exception e) {
            log.warn("Failed to save AI result: {}", e.getMessage());
        }
        return ApiResponse.success("总结生成完成", summary);
    }

    // ── helpers ──

    private void autoAddParticipants(Meeting meeting, Long teamId) {
        List<TeamMember> members = teamMemberRepository.findByTeamId(teamId);
        for (int i = 0; i < members.size(); i++) {
            MeetingParticipant mp = new MeetingParticipant();
            mp.setMeetingId(meeting.getId());
            mp.setUserId(members.get(i).getUserId());
            mp.setSpeechOrder(i + 1);
            participantRepository.save(mp);
        }
    }

    private List<Map<String, Object>> buildParticipantList(List<MeetingParticipant> participants) {
        List<Map<String, Object>> list = new ArrayList<>();
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
            list.add(pm);
        }
        return list;
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
