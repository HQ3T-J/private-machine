package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.Meeting;
import com.standupsync.model.MeetingSpeech;
import com.standupsync.model.User;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.MeetingSpeechRepository;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.service.AIService;
import com.standupsync.config.AIServerConfig;

import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@RestController
@RequestMapping("/api/meetings")
public class SpeechController {

    private final MeetingSpeechRepository meetingSpeechRepository;
    private final MeetingRepository meetingRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final AIService aiService;
    private final AIServerConfig aiConfig;

    public SpeechController(MeetingSpeechRepository meetingSpeechRepository,
                            MeetingRepository meetingRepository,
                            TeamMemberRepository teamMemberRepository,
                            AIService aiService,
                            AIServerConfig aiConfig) {
        this.meetingSpeechRepository = meetingSpeechRepository;
        this.meetingRepository = meetingRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.aiService = aiService;
        this.aiConfig = aiConfig;
    }

    /** 原始结构化三段式发言（兼容旧版） */
    @PostMapping("/{id}/speeches")
    public ApiResponse<MeetingSpeech> submitSpeech(@RequestAttribute("userId") String userId,
                                                    @PathVariable("id") Long meetingId,
                                                    @RequestBody Map<String, String> body) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isMember(userId, meeting.getTeam().getId()))
            return ApiResponse.error(403, "无权在此会议提交发言");

        MeetingSpeech speech = buildSpeech(meeting, userId, body);
        speech = meetingSpeechRepository.save(speech);
        return ApiResponse.success("发言提交成功", speech);
    }

    /**
     * 自由文本发言 — 单输入框，AI 自动解析为结构化数据。
     * Body: {"text": "昨天修了登录bug，今天做dashboard，需要review"}
     * 返回: speech 对象，含 AI 解析的 yesterday/today/blockers
     */
    @PostMapping("/{id}/speeches/free")
    public ApiResponse<Map<String, Object>> submitFreeSpeech(
            @RequestAttribute("userId") String userId,
            @PathVariable("id") Long meetingId,
            @RequestBody Map<String, String> body) {

        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isMember(userId, meeting.getTeam().getId()))
            return ApiResponse.error(403, "无权在此会议提交发言");

        String text = body.getOrDefault("text", "");
        if (text.isBlank()) return ApiResponse.error(400, "发言内容不能为空");

        String inputMethod = body.getOrDefault("inputMethod", "TEXT");

        // AI 解析自由文本（优先LLM，降级规则引擎）
        Map<String, String> parsed = aiService.parseFreeText(text, aiConfig);

        MeetingSpeech speech = new MeetingSpeech();
        speech.setMeeting(meeting);
        User speaker = new User();
        speaker.setId(userId);
        speech.setSpeaker(speaker);
        speech.setRawText(text);
        speech.setYesterday(parsed.get("yesterday"));
        speech.setToday(parsed.get("today"));
        speech.setBlockers(parsed.get("blockers"));
        speech.setInputMethod(mapInputMethod(inputMethod));
        speech = meetingSpeechRepository.save(speech);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("speech", speech);
        result.put("parsed", parsed);
        return ApiResponse.success("发言已提交并解析", result);
    }

    @GetMapping("/{id}/speeches")
    public ApiResponse<List<MeetingSpeech>> listSpeeches(@RequestAttribute("userId") String userId,
                                                          @PathVariable("id") Long meetingId) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isMember(userId, meeting.getTeam().getId()))
            return ApiResponse.error(403, "无权查看该会议发言");
        return ApiResponse.success(
            meetingSpeechRepository.findByMeetingIdOrderByCreatedAtAsc(meetingId));
    }

    @PostMapping("/{id}/parse-chat")
    public ApiResponse<Map<String, Object>> parseChat(@RequestAttribute("userId") String userId,
                                                       @PathVariable("id") Long meetingId,
                                                       @RequestBody Map<String, String> body) {
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "会议不存在");
        if (!isMember(userId, meeting.getTeam().getId()))
            return ApiResponse.error(403, "无权解析该会议聊天");

        String rawChat = body.get("chatText");
        if (rawChat == null) rawChat = body.get("chatContent");

        Map<String, Object> result = new HashMap<>();
        result.put("meetingId", meetingId);

        if (rawChat != null && !rawChat.isBlank()) {
            List<Map<String, String>> speeches = new ArrayList<>();
            String[] lines = rawChat.split("\\R");
            String currentSpeaker = null;
            StringBuilder currentContent = new StringBuilder();

            for (String line : lines) {
                String trimmed = line.trim();
                if (trimmed.isEmpty()) continue;
                int colonIdx = -1;
                int cpEn = trimmed.indexOf(':'), cpCn = trimmed.indexOf('：');
                if (cpEn > 0 && (cpCn < 0 || cpEn < cpCn)) colonIdx = cpEn;
                else if (cpCn > 0) colonIdx = cpCn;

                if (colonIdx > 0 && colonIdx < 30) {
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

    // ── helper methods ──

    private MeetingSpeech buildSpeech(Meeting meeting, String userId, Map<String, String> body) {
        MeetingSpeech speech = new MeetingSpeech();
        speech.setMeeting(meeting);
        User speaker = new User(); speaker.setId(userId);
        speech.setSpeaker(speaker);

        String yesterday = body.get("yesterday"), today = body.get("today"), blockers = body.get("blockers");
        String rawText = body.get("rawText"), content = body.get("content");

        if (yesterday != null || today != null || blockers != null) {
            speech.setYesterday(yesterday); speech.setToday(today); speech.setBlockers(blockers);
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

        speech.setInputMethod(mapInputMethod(body.get("inputMethod")));
        return speech;
    }

    private MeetingSpeech.InputMethod mapInputMethod(String im) {
        if ("VOICE".equalsIgnoreCase(im)) return MeetingSpeech.InputMethod.VOICE;
        if ("PASTE".equalsIgnoreCase(im)) return MeetingSpeech.InputMethod.PASTE;
        return MeetingSpeech.InputMethod.TEXT;
    }

    private boolean isMember(String userId, Long teamId) {
        return teamMemberRepository.existsByTeamIdAndUserId(teamId, userId);
    }
}
