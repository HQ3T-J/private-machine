package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.*;
import com.standupsync.repository.*;

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
        result.put("team", meeting.getTeam());
        result.put("participants", participantList);
        return ApiResponse.success(result);
    }

    @GetMapping
    public ApiResponse<List<Meeting>> listMeetings(@RequestAttribute("userId") String userId,
                                                    @RequestParam("teamId") Long teamId) {
        if (!isMember(userId, teamId)) return ApiResponse.error(403, "无权查看该团队的会议");
        return ApiResponse.success(meetingRepository.findByTeamIdOrderByCreatedAtDesc(teamId));
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
