package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.service.DashboardService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.*;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    private final DashboardService service;

    public DashboardController(DashboardService service) {
        this.service = service;
    }

    @GetMapping("/kpi")
    public ApiResponse<Map<String, Object>> kpi(
            @RequestParam Long teamId,
            @RequestParam(required = false) String sprintNo,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateTo) {
        return ApiResponse.ok(service.computeSummary(teamId, sprintNo, dateFrom, dateTo));
    }

    @GetMapping("/trends")
    public ApiResponse<Map<String, Object>> trends(
            @RequestParam Long teamId,
            @RequestParam(required = false) String userId) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("attendance", service.computeAttendanceTrend(teamId, 10, userId));
        result.put("completion", service.computeCompletionTrend(teamId, 10, userId));
        return ApiResponse.ok(result);
    }

    @GetMapping("/summary")
    public ApiResponse<Map<String, Object>> summary(
            @RequestParam Long teamId,
            @RequestParam(required = false) String sprintNo,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateTo) {
        return ApiResponse.ok(service.computeSummary(teamId, sprintNo, dateFrom, dateTo));
    }

    @GetMapping("/attendance-trend")
    public ApiResponse<List<Map<String, Object>>> attendanceTrend(
            @RequestParam Long teamId,
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(required = false) String userId) {
        return ApiResponse.ok(service.computeAttendanceTrend(teamId, limit, userId));
    }

    @GetMapping("/completion-trend")
    public ApiResponse<List<Map<String, Object>>> completionTrend(
            @RequestParam Long teamId,
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(required = false) String userId) {
        return ApiResponse.ok(service.computeCompletionTrend(teamId, limit, userId));
    }

    @GetMapping("/completion-trend-daily")
    public ApiResponse<List<Map<String, Object>>> completionTrendDaily(
            @RequestParam Long teamId,
            @RequestParam(defaultValue = "7") int days) {
        return ApiResponse.ok(service.computeCompletionTrendDaily(teamId, days));
    }

    @GetMapping("/blocker-distribution")
    public ApiResponse<List<Map<String, Object>>> blockerDistribution(
            @RequestParam Long teamId,
            @RequestParam(required = false) String blockerType) {
        return ApiResponse.ok(service.computeBlockerDistribution(teamId, blockerType));
    }

    @GetMapping("/member-ranking")
    public ApiResponse<List<Map<String, Object>>> memberRanking(
            @RequestParam Long teamId,
            @RequestParam(defaultValue = "completionRate") String sortBy) {
        return ApiResponse.ok(service.computeMemberRanking(teamId, sortBy));
    }

    @GetMapping("/export")
    public ApiResponse<Map<String, String>> exportCsv(
            @RequestParam Long teamId,
            @RequestParam(defaultValue = "meetings") String type) {
        String content;
        String filename;
        switch (type) {
            case "meetings" -> {
                content = service.exportMeetingsCsv(teamId);
                filename = "meetings.csv";
            }
            case "action-items" -> {
                content = service.exportActionItemsCsv(teamId);
                filename = "action_items.csv";
            }
            default -> { return ApiResponse.error(400, "不支持的导出类型: " + type); }
        }
        Map<String, String> result = new LinkedHashMap<>();
        result.put("content", content);
        result.put("filename", filename);
        result.put("format", "csv");
        return ApiResponse.ok(result);
    }
}
