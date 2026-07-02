package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.Notification;
import com.standupsync.service.NotificationService;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class NotificationController {

    private final NotificationService notificationService;

    public NotificationController(NotificationService notificationService) {
        this.notificationService = notificationService;
    }

    @GetMapping("/notifications")
    public ApiResponse<List<Notification>> getAllNotifications(
            @RequestAttribute("userId") String userId) {
        try {
            List<Notification> list = notificationService.getAll(userId);
            return ApiResponse.ok(list);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @GetMapping("/notifications/unread")
    public ApiResponse<List<Notification>> getUnreadNotifications(
            @RequestAttribute("userId") String userId) {
        try {
            List<Notification> list = notificationService.getUnread(userId);
            return ApiResponse.ok(list);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @GetMapping("/notifications/count")
    public ApiResponse<Map<String, Object>> getNotificationCount(
            @RequestAttribute("userId") String userId) {
        try {
            Map<String, Object> stats = notificationService.getStats(userId);
            return ApiResponse.ok(stats);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @PostMapping("/notifications/{id}/read")
    public ApiResponse<Void> markAsRead(
            @PathVariable Long id) {
        try {
            notificationService.markAsRead(id);
            return ApiResponse.ok("已标记", null);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @PostMapping("/notifications/read-all")
    public ApiResponse<Void> markAllAsRead(
            @RequestAttribute("userId") String userId) {
        try {
            notificationService.markAllAsRead(userId);
            return ApiResponse.ok("已全部已读", null);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }
}
