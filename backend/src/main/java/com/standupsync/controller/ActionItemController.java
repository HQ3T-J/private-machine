package com.standupsync.controller;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.standupsync.dto.ApiResponse;
import com.standupsync.model.ActionItem;
import com.standupsync.model.Meeting;
import com.standupsync.model.User;
import com.standupsync.repository.ActionItemRepository;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.UserRepository;
import com.standupsync.service.ActionItemService;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api")
public class ActionItemController {

    private final ActionItemService actionItemService;
    private final ActionItemRepository actionItemRepo;
    private final MeetingRepository meetingRepo;
    private final UserRepository userRepo;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ActionItemController(ActionItemService actionItemService,
                                ActionItemRepository actionItemRepo,
                                MeetingRepository meetingRepo,
                                UserRepository userRepo) {
        this.actionItemService = actionItemService;
        this.actionItemRepo = actionItemRepo;
        this.meetingRepo = meetingRepo;
        this.userRepo = userRepo;
    }

    @GetMapping("/action-items")
    public ApiResponse<?> list(@RequestAttribute("userId") String userId,
                                @RequestParam(required = false) String status) {
        return actionItemService.listByUser(userId, status);
    }

    @GetMapping("/todos/unfinished")
    public ApiResponse<?> unfinished(@RequestAttribute("userId") String userId) {
        return actionItemService.unfinished(userId);
    }

    @GetMapping("/action-items/team")
    public ApiResponse<?> listByTeam(@RequestParam Long teamId,
                                      @RequestParam(required = false) String status) {
        return actionItemService.listByTeam(teamId, status);
    }

    @PostMapping("/action-items")
    public ApiResponse<?> create(@RequestAttribute("userId") String userId,
                                  @RequestBody Map<String, Object> body) {
        return actionItemService.create(userId, body);
    }

    @PutMapping("/action-items/{id}")
    public ApiResponse<?> update(@RequestAttribute("userId") String userId,
                                  @PathVariable Long id,
                                  @RequestBody Map<String, Object> body) {
        return actionItemService.update(userId, id, body);
    }

    @DeleteMapping("/action-items/{id}")
    public ApiResponse<?> delete(@RequestAttribute("userId") String userId,
                                  @PathVariable Long id) {
        return actionItemService.delete(userId, id);
    }

    @PutMapping("/action-items/{item_id}/status")
    public ApiResponse<?> updateStatus(@RequestAttribute("userId") String userId,
                                        @PathVariable("item_id") Long itemId,
                                        @RequestParam String status) {
        return actionItemService.updateStatus(userId, itemId, status);
    }

    // ═══ 站会关联操作（轻量，保留在Controller） ═══

    @GetMapping("/meetings/{id}/unfinished-items")
    public ApiResponse<?> meetingUnfinished(@PathVariable Long id) {
        Meeting meeting = meetingRepo.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        List<Meeting> meetings = meetingRepo.findByTeamIdOrderByCreatedAtDesc(meeting.getTeam().getId());
        Meeting prev = null;
        for (Meeting m : meetings) { if (m.getId() < id) { prev = m; break; } }
        if (prev == null) return ApiResponse.ok(Collections.emptyList());
        List<ActionItem> items = actionItemRepo.findByMeetingId(prev.getId());
        items = items.stream()
                .filter(i -> i.getStatus() != ActionItem.ActionItemStatus.DONE
                          && i.getStatus() != ActionItem.ActionItemStatus.CANCELLED)
                .toList();
        return ApiResponse.ok(items);
    }

    @PutMapping("/meetings/{id}/confirm-items")
    public ApiResponse<?> confirm(@PathVariable Long id,
                                   @RequestBody List<Map<String, Object>> updates) {
        List<ActionItem> updated = new ArrayList<>();
        for (Map<String, Object> u : updates) {
            Long itemId = Long.valueOf(u.get("id").toString());
            ActionItem item = actionItemRepo.findById(itemId).orElse(null);
            if (item == null) continue;
            ActionItem.ActionItemStatus old = item.getStatus();
            ActionItem.ActionItemStatus ns = ActionItem.ActionItemStatus.valueOf(
                ((String) u.get("status")).toUpperCase());
            item.setStatus(ns);
            if (ns == ActionItem.ActionItemStatus.DONE && old != ActionItem.ActionItemStatus.DONE)
                item.setCompletedAt(LocalDateTime.now());
            updated.add(actionItemRepo.save(item));
        }
        return ApiResponse.ok(updated);
    }

    @PostMapping("/meetings/{id}/generate-action-items")
    public ApiResponse<?> generate(@RequestAttribute("userId") String userId,
                                    @PathVariable("id") Long meetingId) {
        Meeting meeting = meetingRepo.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        if (meeting.getAiResult() == null || meeting.getAiResult().isBlank())
            return ApiResponse.error(400, "该站会尚无 AI 分析结果");

        try {
            Map<String, Object> aiResult = objectMapper.readValue(meeting.getAiResult(),
                    new TypeReference<Map<String, Object>>() {});
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> actionItems =
                    (List<Map<String, Object>>) aiResult.getOrDefault("action_items", Collections.emptyList());
            return ApiResponse.ok(Map.of("count", actionItems.size(), "message", "解析完成"));
        } catch (Exception e) {
            return ApiResponse.error(500, "AI 结果解析失败: " + e.getMessage());
        }
    }
}
