package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.Meeting;
import com.standupsync.model.MeetingSpeech;
import com.standupsync.model.Team;
import com.standupsync.model.TeamMember;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.MeetingSpeechRepository;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.repository.TeamRepository;

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

    public MeetingController(MeetingRepository meetingRepository,
                             MeetingSpeechRepository meetingSpeechRepository,
                             TeamMemberRepository teamMemberRepository,
                             TeamRepository teamRepository) {
        this.meetingRepository = meetingRepository;
        this.meetingSpeechRepository = meetingSpeechRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.teamRepository = teamRepository;
    }

    @PostMapping
    public ApiResponse<Meeting> createMeeting(@RequestAttribute("userId") String userId,
                                               @RequestBody Map<String, Object> body) {
        Object teamIdObj = body.get("teamId");
        if (teamIdObj == null) {
            return ApiResponse.error(400, "teamId 不能为空");
        }
        Long teamId = Long.valueOf(teamIdObj.toString());
        if (!isMember(userId, teamId)) {
            return ApiResponse.error(403, "无权在该团队创建会议");
        }

        Team team = teamRepository.findById(teamId).orElse(null);
        if (team == null) {
            return ApiResponse.error(404, "团队不存在");
        }

        Meeting meeting = new Meeting();
        meeting.setTeam(team);
        meeting.setCreatedBy(userId);

        // title 支持
        if (body.containsKey("title") && body.get("title") != null) {
            meeting.setTitle(body.get("title").toString());
        }

        Integer sprintNo = body.containsKey("sprintNo") ? ((Number) body.get("sprintNo")).intValue() : 1;
        meeting.setSprintNo(sprintNo);
        String formType = body.containsKey("formType") ? body.get("formType").toString() : "REALTIME";
        meeting.setFormType(Meeting.FormType.valueOf(formType));
        meeting.setStatus(Meeting.MeetingStatus.CREATED);
        meeting.setAiStatus(Meeting.AiStatus.IDLE);
        meeting = meetingRepository.save(meeting);
        return ApiResponse.success("会议创建成功", meeting);
    }

    @GetMapping("/{id}")
    public ApiResponse<Meeting> getMeeting(@RequestAttribute("userId") String userId,
                                           @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) {
            return ApiResponse.error(404, "会议不存在");
        }
        if (!isMember(userId, meeting.getTeam().getId())) {
            return ApiResponse.error(403, "无权访问该会议");
        }
        return ApiResponse.success(meeting);
    }

    @GetMapping
    public ApiResponse<List<Meeting>> listMeetings(@RequestAttribute("userId") String userId,
                                                    @RequestParam("teamId") Long teamId) {
        if (!isMember(userId, teamId)) {
            return ApiResponse.error(403, "无权查看该团队的会议");
        }
        List<Meeting> meetings = meetingRepository.findByTeamIdOrderByCreatedAtDesc(teamId);
        return ApiResponse.success(meetings);
    }

    @PostMapping("/{id}/start")
    public ApiResponse<Meeting> startMeeting(@RequestAttribute("userId") String userId,
                                              @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) {
            return ApiResponse.error(404, "会议不存在");
        }
        if (!isAdmin(userId, meeting.getTeam().getId())) {
            return ApiResponse.error(403, "只有管理员可以开始会议");
        }
        if (meeting.getStatus() != Meeting.MeetingStatus.CREATED) {
            return ApiResponse.error(400, "会议状态不允许开始");
        }

        meeting.setStatus(Meeting.MeetingStatus.ACTIVE);
        meeting = meetingRepository.save(meeting);
        return ApiResponse.success("会议已开始", meeting);
    }

    @PostMapping("/{id}/end")
    public ApiResponse<Meeting> endMeeting(@RequestAttribute("userId") String userId,
                                            @PathVariable Long id) {
        Meeting meeting = meetingRepository.findById(id).orElse(null);
        if (meeting == null) {
            return ApiResponse.error(404, "会议不存在");
        }
        if (!isAdmin(userId, meeting.getTeam().getId())) {
            return ApiResponse.error(403, "只有管理员可以结束会议");
        }
        if (meeting.getStatus() != Meeting.MeetingStatus.ACTIVE) {
            return ApiResponse.error(400, "会议未在进行中，无法结束");
        }

        meeting.setStatus(Meeting.MeetingStatus.ENDED);
        meeting.setEndedAt(LocalDateTime.now());
        meeting = meetingRepository.save(meeting);
        return ApiResponse.success("会议已结束", meeting);
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
