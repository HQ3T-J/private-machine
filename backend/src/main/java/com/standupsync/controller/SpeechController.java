package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.Meeting;
import com.standupsync.model.MeetingSpeech;
import com.standupsync.model.User;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.MeetingSpeechRepository;
import com.standupsync.repository.TeamMemberRepository;

import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/meetings")
public class SpeechController {

    private final MeetingSpeechRepository meetingSpeechRepository;
    private final MeetingRepository meetingRepository;
    private final TeamMemberRepository teamMemberRepository;

    public SpeechController(MeetingSpeechRepository meetingSpeechRepository,
                            MeetingRepository meetingRepository,
                            TeamMemberRepository teamMemberRepository) {
        this.meetingSpeechRepository = meetingSpeechRepository;
        this.meetingRepository = meetingRepository;
        this.teamMemberRepository = teamMemberRepository;
    }

    @PostMapping("/{id}/speeches")
    public ApiResponse<MeetingSpeech> submitSpeech(@RequestAttribute("userId") String userId,
                                                    @PathVariable("id") Long meetingId,
                                                    @RequestBody Map<String, String> body) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) {
            return ApiResponse.error(404, "会议不存在");
        }
        if (!isMember(userId, meeting.getTeam().getId())) {
            return ApiResponse.error(403, "无权在此会议提交发言");
        }

        MeetingSpeech speech = new MeetingSpeech();
        speech.setMeeting(meeting);
        User speaker = new User();
        speaker.setId(userId);
        speech.setSpeaker(speaker);

        // 结构化三段式发言（优先），兼容旧的 rawText
        String yesterday = body.get("yesterday");
        String today = body.get("today");
        String blockers = body.get("blockers");
        String rawText = body.get("rawText");
        String content = body.get("content");

        if (yesterday != null || today != null || blockers != null) {
            // 结构化模式
            speech.setYesterday(yesterday);
            speech.setToday(today);
            speech.setBlockers(blockers);
            // 合并为 rawText 便于 AI 分析
            StringBuilder sb = new StringBuilder();
            if (yesterday != null && !yesterday.isBlank()) sb.append("昨日: ").append(yesterday).append("\n");
            if (today != null && !today.isBlank()) sb.append("今日: ").append(today).append("\n");
            if (blockers != null && !blockers.isBlank()) sb.append("阻碍: ").append(blockers);
            speech.setRawText(sb.toString().trim());
        } else if (rawText != null && !rawText.isBlank()) {
            speech.setRawText(rawText);
        } else if (content != null && !content.isBlank()) {
            speech.setRawText(content);
        }

        // 输入方式
        String inputMethod = body.get("inputMethod");
        if ("VOICE".equalsIgnoreCase(inputMethod)) {
            speech.setInputMethod(MeetingSpeech.InputMethod.VOICE);
        } else if ("PASTE".equalsIgnoreCase(inputMethod)) {
            speech.setInputMethod(MeetingSpeech.InputMethod.PASTE);
        } else {
            speech.setInputMethod(MeetingSpeech.InputMethod.TEXT);
        }

        speech = meetingSpeechRepository.save(speech);
        return ApiResponse.success("发言提交成功", speech);
    }

    @GetMapping("/{id}/speeches")
    public ApiResponse<List<MeetingSpeech>> listSpeeches(@RequestAttribute("userId") String userId,
                                                          @PathVariable("id") Long meetingId) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) {
            return ApiResponse.error(404, "会议不存在");
        }
        if (!isMember(userId, meeting.getTeam().getId())) {
            return ApiResponse.error(403, "无权查看该会议发言");
        }
        List<MeetingSpeech> speeches = meetingSpeechRepository.findByMeetingIdOrderByCreatedAtAsc(meetingId);
        return ApiResponse.success(speeches);
    }

    @PostMapping("/{id}/parse-chat")
    public ApiResponse<Map<String, Object>> parseChat(@RequestAttribute("userId") String userId,
                                                       @PathVariable("id") Long meetingId,
                                                       @RequestBody Map<String, String> body) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) {
            return ApiResponse.error(404, "会议不存在");
        }
        if (!isMember(userId, meeting.getTeam().getId())) {
            return ApiResponse.error(403, "无权解析该会议聊天");
        }

        String rawChat = body.get("chatText");
        if (rawChat == null) rawChat = body.get("chatContent");

        Map<String, Object> result = new HashMap<>();
        result.put("meetingId", meetingId);

        if (rawChat != null && !rawChat.isBlank()) {
            // 按 "Name: content" 模式解析
            List<Map<String, String>> speeches = new ArrayList<>();
            String[] lines = rawChat.split("\\R");
            String currentSpeaker = null;
            StringBuilder currentContent = new StringBuilder();

            for (String line : lines) {
                String trimmed = line.trim();
                if (trimmed.isEmpty()) continue;

                // 检测 "Name: content" 或 "Name： content"
                int colonIdx = -1;
                int colonPosEn = trimmed.indexOf(':');
                int colonPosCn = trimmed.indexOf('：');
                if (colonPosEn > 0 && (colonPosCn < 0 || colonPosEn < colonPosCn)) {
                    colonIdx = colonPosEn;
                } else if (colonPosCn > 0) {
                    colonIdx = colonPosCn;
                }

                if (colonIdx > 0 && colonIdx < 30) {
                    // 新发言人
                    if (currentSpeaker != null && currentContent.length() > 0) {
                        Map<String, String> item = new HashMap<>();
                        item.put("speaker", currentSpeaker);
                        item.put("content", currentContent.toString().trim());
                        speeches.add(item);
                    }
                    currentSpeaker = trimmed.substring(0, colonIdx).trim();
                    currentContent = new StringBuilder(trimmed.substring(colonIdx + 1).trim());
                } else if (currentSpeaker != null) {
                    currentContent.append("\n").append(trimmed);
                }
            }
            if (currentSpeaker != null && currentContent.length() > 0) {
                Map<String, String> item = new HashMap<>();
                item.put("speaker", currentSpeaker);
                item.put("content", currentContent.toString().trim());
                speeches.add(item);
            }
            result.put("speeches", speeches);
        } else {
            result.put("speeches", Collections.emptyList());
        }
        return ApiResponse.success(result);
    }

    private boolean isMember(String userId, Long teamId) {
        return teamMemberRepository.existsByTeamIdAndUserId(teamId, userId);
    }
}
