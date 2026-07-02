package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.service.MeetingService;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/meetings")
public class MeetingController {

    private final MeetingService meetingService;

    public MeetingController(MeetingService meetingService) {
        this.meetingService = meetingService;
    }

    @PostMapping
    public ApiResponse<?> createMeeting(@RequestAttribute("userId") String userId,
                                         @RequestBody Map<String, Object> body) {
        return meetingService.createMeeting(userId, body);
    }

    @GetMapping("/{id}")
    public ApiResponse<?> getMeeting(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id) {
        return meetingService.getMeeting(userId, id);
    }

    @GetMapping
    public ApiResponse<?> listMeetings(@RequestAttribute("userId") String userId,
                                        @RequestParam("teamId") Long teamId,
                                        @RequestParam(defaultValue = "0") int page,
                                        @RequestParam(defaultValue = "20") int size) {
        return meetingService.listMeetings(userId, teamId, page, size);
    }

    @PostMapping("/{id}/start")
    public ApiResponse<?> startMeeting(@RequestAttribute("userId") String userId,
                                        @PathVariable Long id) {
        return meetingService.startMeeting(userId, id);
    }

    @PostMapping("/{id}/end")
    public ApiResponse<?> endMeeting(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id) {
        return meetingService.endMeeting(userId, id);
    }

    @PostMapping("/{id}/paste")
    public ApiResponse<?> pasteChat(@RequestAttribute("userId") String userId,
                                     @PathVariable Long id,
                                     @RequestBody Map<String, String> body) {
        return meetingService.pasteChat(id, body.getOrDefault("text", ""));
    }

    @PostMapping("/{id}/classify")
    public ApiResponse<?> classifyText(@RequestAttribute("userId") String userId,
                                        @PathVariable Long id,
                                        @RequestBody Map<String, String> body) {
        String text = body.getOrDefault("text", "");
        if (text.isBlank()) return ApiResponse.error(400, "文本为空");
        String t = text.toLowerCase();
        int ys = t.contains("昨天") || t.contains("完成") ? 10 : 0;
        int ts = t.contains("今天") || t.contains("计划") ? 10 : 0;
        int bs = t.contains("阻碍") || t.contains("问题") ? 10 : 0;
        String cat = ys >= ts && ys >= bs ? "yesterday" : bs >= ts ? "blocker" : "today";
        return ApiResponse.success(Map.of("category", cat, "confidence", 0.7));
    }

    @PostMapping("/{id}/summary/generate")
    public ApiResponse<?> generateSummary(@RequestAttribute("userId") String userId,
                                           @PathVariable Long id) {
        return meetingService.generateSummary(userId, id);
    }

    @GetMapping("/{id}/summary")
    public ApiResponse<?> getSummary(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id) {
        return ApiResponse.success(Map.of("standupId", id, "aiStatus", "IDLE"));
    }

    @PutMapping("/summary/items/{itemId}")
    public ApiResponse<?> updateSummaryItem(@PathVariable Long itemId,
                                             @RequestBody Map<String, String> body) {
        return ApiResponse.success("已更新", body);
    }
}
