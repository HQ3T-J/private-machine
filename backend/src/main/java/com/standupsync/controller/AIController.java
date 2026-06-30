package com.standupsync.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.standupsync.dto.ApiResponse;
import com.standupsync.model.Meeting;
import com.standupsync.model.MeetingSpeech;
import com.standupsync.model.User;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.MeetingSpeechRepository;
import com.standupsync.repository.UserRepository;
import com.standupsync.service.AIService;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/meetings")
public class AIController {

    private final MeetingRepository meetingRepo;
    private final MeetingSpeechRepository speechRepo;
    private final UserRepository userRepo;
    private final AIService aiService;

    public AIController(MeetingRepository meetingRepo, MeetingSpeechRepository speechRepo,
                        UserRepository userRepo, AIService aiService) {
        this.meetingRepo = meetingRepo;
        this.speechRepo = speechRepo;
        this.userRepo = userRepo;
        this.aiService = aiService;
    }

    @PostMapping("/{id}/analyze")
    public ApiResponse<Map<String, String>> analyze(@PathVariable Long id,
                                                     @RequestAttribute("userId") String userId) {
        Meeting meeting = meetingRepo.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        if (meeting.getStatus() != Meeting.MeetingStatus.ACTIVE) {
            return ApiResponse.error(400, "站会未在进行中");
        }

        meeting.setAiStatus(Meeting.AiStatus.PROCESSING);
        meetingRepo.save(meeting);

        // Async: trigger analysis in background (simplified - runs sync for now)
        User user = userRepo.findById(userId).orElse(null);
        List<MeetingSpeech> speeches = speechRepo.findByMeetingIdOrderByCreatedAtAsc(id);

        try {
            User.AIConfig aiConfig = user != null ? new User.AIConfig(
            user.getAiProvider(), user.getAiModel(), user.getAiApiKey()) : new User.AIConfig();
        String result = new ObjectMapper().writeValueAsString(aiService.analyzeMeeting(speeches, aiConfig));
            meeting.setAiResult(result);
            meeting.setAiStatus(Meeting.AiStatus.DONE);
        } catch (Exception e) {
            meeting.setAiStatus(Meeting.AiStatus.FAILED);
            meeting.setAiError(e.getMessage());
        }
        meetingRepo.save(meeting);

        return ApiResponse.ok(Map.of("aiStatus", meeting.getAiStatus().name()));
    }

    @GetMapping("/{id}/ai-status")
    public ApiResponse<Map<String, Object>> aiStatus(@PathVariable Long id) {
        Meeting meeting = meetingRepo.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        Map<String, Object> result = new HashMap<>();
        result.put("aiStatus", meeting.getAiStatus().name());
        if (meeting.getAiStatus() == Meeting.AiStatus.DONE) {
            result.put("aiResult", meeting.getAiResult());
        }
        if (meeting.getAiStatus() == Meeting.AiStatus.FAILED) {
            result.put("aiError", meeting.getAiError());
        }
        return ApiResponse.ok(result);
    }

    @PutMapping("/{id}/ai-result")
    public ApiResponse<Meeting> saveResult(@PathVariable Long id,
                                            @RequestBody Map<String, Object> body) {
        Meeting meeting = meetingRepo.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        if (body.containsKey("aiResult")) {
            meeting.setAiResult(body.get("aiResult").toString());
        }
        return ApiResponse.ok(meetingRepo.save(meeting));
    }
}
