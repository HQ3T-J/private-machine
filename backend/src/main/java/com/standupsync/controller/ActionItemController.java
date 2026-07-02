package com.standupsync.controller;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.standupsync.dto.ApiResponse;
import com.standupsync.model.ActionItem;
import com.standupsync.model.Meeting;
import com.standupsync.model.User;
import com.standupsync.model.Team;
import com.standupsync.repository.ActionItemRepository;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.UserRepository;
import com.standupsync.repository.TeamRepository;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api")
public class ActionItemController {

    private final ActionItemRepository repo;
    private final MeetingRepository meetingRepo;
    private final UserRepository userRepo;
    private final TeamRepository teamRepo;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ActionItemController(ActionItemRepository repo, MeetingRepository meetingRepo,
                                UserRepository userRepo, TeamRepository teamRepo) {
        this.repo = repo;
        this.meetingRepo = meetingRepo;
        this.userRepo = userRepo;
        this.teamRepo = teamRepo;
    }

    @GetMapping("/action-items")
    public ApiResponse<List<ActionItem>> list(@RequestAttribute("userId") String userId,
                                               @RequestParam(required = false) String status) {
        List<ActionItem> items = repo.findByAssigneeId(userId);
        if (status != null) {
            items = items.stream().filter(i -> i.getStatus().name().equalsIgnoreCase(status)).toList();
        }
        return ApiResponse.ok(items);
    }

    @GetMapping("/todos/unfinished")
    public ApiResponse<List<ActionItem>> unfinished(@RequestAttribute("userId") String userId) {
        List<ActionItem> items = repo.findByAssigneeId(userId);
        items = items.stream()
                .filter(i -> !"DONE".equalsIgnoreCase(i.getStatus().name())
                          && !"completed".equalsIgnoreCase(i.getStatus().name()))
                .toList();
        return ApiResponse.ok(items);
    }

    @GetMapping("/action-items/team")
    public ApiResponse<List<ActionItem>> listByTeam(@RequestParam Long teamId,
                                                     @RequestParam(required = false) String status) {
        if (status != null) {
            return ApiResponse.ok(repo.findByTeamIdAndStatus(teamId,
                ActionItem.ActionItemStatus.valueOf(status.toUpperCase())));
        }
        return ApiResponse.ok(repo.findByTeamId(teamId));
    }

    @PostMapping("/action-items")
    public ApiResponse<ActionItem> create(@RequestAttribute("userId") String userId,
                                           @RequestBody Map<String, Object> body) {
        ActionItem item = new ActionItem();
        item.setContent((String) body.get("content"));
        if (body.containsKey("assigneeId")) {
            userRepo.findById((String) body.get("assigneeId")).ifPresent(item::setAssignee);
        } else {
            userRepo.findById(userId).ifPresent(item::setAssignee);
        }
        userRepo.findById(userId).ifPresent(item::setAssigner);
        if (body.containsKey("teamId")) {
            teamRepo.findById(Long.valueOf(body.get("teamId").toString())).ifPresent(item::setTeam);
        }
        if (body.containsKey("meetingId")) {
            meetingRepo.findById(Long.valueOf(body.get("meetingId").toString())).ifPresent(item::setMeeting);
        }
        if (body.containsKey("status")) {
            ActionItem.ActionItemStatus oldStatus = item.getStatus();
            ActionItem.ActionItemStatus newStatus = ActionItem.ActionItemStatus.valueOf(
                ((String) body.get("status")).toUpperCase());
            item.setStatus(newStatus);
            updateCompletedAt(item, oldStatus, newStatus);
        }
        if (body.containsKey("priority")) {
            item.setPriority(ActionItem.Priority.valueOf(((String) body.get("priority")).toUpperCase()));
        }
        if (body.containsKey("confirmed")) {
            item.setConfirmed(Boolean.valueOf(body.get("confirmed").toString()));
        }
        return ApiResponse.ok(repo.save(item));
    }

    @PutMapping("/action-items/{id}")
    public ApiResponse<ActionItem> update(@RequestAttribute("userId") String userId,
                                           @PathVariable Long id,
                                           @RequestBody Map<String, Object> body) {
        ActionItem item = repo.findById(id).orElse(null);
        if (item == null) return ApiResponse.error(404, "待办不存在");
        if (body.containsKey("content")) item.setContent((String) body.get("content"));
        if (body.containsKey("status")) {
            ActionItem.ActionItemStatus oldStatus = item.getStatus();
            ActionItem.ActionItemStatus newStatus = ActionItem.ActionItemStatus.valueOf(
                ((String) body.get("status")).toUpperCase());
            item.setStatus(newStatus);
            updateCompletedAt(item, oldStatus, newStatus);
        }
        if (body.containsKey("priority")) {
            item.setPriority(ActionItem.Priority.valueOf(((String) body.get("priority")).toUpperCase()));
        }
        if (body.containsKey("assigneeId")) {
            userRepo.findById((String) body.get("assigneeId")).ifPresent(item::setAssignee);
        } else {
            userRepo.findById(userId).ifPresent(item::setAssignee);
        }
        if (body.containsKey("confirmed")) {
            item.setConfirmed(Boolean.valueOf(body.get("confirmed").toString()));
        }
        return ApiResponse.ok(repo.save(item));
    }

@DeleteMapping("/action-items/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        repo.deleteById(id);
        return ApiResponse.ok("已删除", null);
    }

    @GetMapping("/meetings/{id}/unfinished-items")
    public ApiResponse<List<ActionItem>> unfinished(@PathVariable Long id) {
        Meeting meeting = meetingRepo.findById(id).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        List<Meeting> meetings = meetingRepo.findByTeamIdOrderByCreatedAtDesc(meeting.getTeam().getId());
        Meeting prev = null;
        for (Meeting m : meetings) {
            if (m.getId() < id) { prev = m; break; }
        }
        if (prev == null) return ApiResponse.ok(Collections.emptyList());
        List<ActionItem> items = repo.findByMeetingId(prev.getId());
        items.removeIf(i -> i.getStatus() == ActionItem.ActionItemStatus.DONE
                         || i.getStatus() == ActionItem.ActionItemStatus.CANCELLED);
        return ApiResponse.ok(items);
    }

    @PutMapping("/meetings/{id}/confirm-items")
    public ApiResponse<List<ActionItem>> confirm(@PathVariable Long id,
                                                  @RequestBody List<Map<String, Object>> updates) {
        List<ActionItem> updated = new ArrayList<>();
        for (Map<String, Object> u : updates) {
            Long itemId = Long.valueOf(u.get("id").toString());
            ActionItem item = repo.findById(itemId).orElse(null);
            if (item == null) continue;
            ActionItem.ActionItemStatus oldStatus = item.getStatus();
            ActionItem.ActionItemStatus newStatus = ActionItem.ActionItemStatus.valueOf(
                ((String) u.get("status")).toUpperCase());
            item.setStatus(newStatus);
            updateCompletedAt(item, oldStatus, newStatus);
            updated.add(repo.save(item));
        }
        return ApiResponse.ok(updated);
    }

    @PutMapping("/action-items/{item_id}/status")
    public ApiResponse<Map<String, String>> updateActionItemStatus(
            @RequestAttribute("userId") String userId,
            @PathVariable("item_id") Long itemId,
            @RequestParam String status) {
        ActionItem item = repo.findById(itemId).orElse(null);
        if (item == null) return ApiResponse.error(404, "待办不存在");
        if (!status.matches("pending|in_progress|reviewing|done|cancelled"))
            return ApiResponse.error(400, "无效状态: " + status);
        ActionItem.ActionItemStatus oldStatus = item.getStatus();
        ActionItem.ActionItemStatus newStatus = ActionItem.ActionItemStatus.valueOf(status.toUpperCase());
        item.setStatus(newStatus);
        updateCompletedAt(item, oldStatus, newStatus);
        repo.save(item);
        return ApiResponse.ok("状态已更新", Map.of("status", item.getStatus().name()));
    }

    /**
     * 从 AI 分析结果自动生成待办项（移植自 Python generate-action-items）
     */
    @PostMapping("/meetings/{id}/generate-action-items")
    public ApiResponse<Map<String, Object>> generateActionItems(
            @RequestAttribute("userId") String userId,
            @PathVariable("id") Long meetingId) {

        Meeting meeting = meetingRepo.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        if (meeting.getAiResult() == null || meeting.getAiResult().isBlank()) {
            return ApiResponse.error(400, "该站会尚无 AI 分析结果，请先执行分析");
        }

        try {
            Map<String, Object> aiResult = objectMapper.readValue(meeting.getAiResult(),
                    new TypeReference<Map<String, Object>>() {});

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> actionItems =
                    (List<Map<String, Object>>) aiResult.getOrDefault("action_items", Collections.emptyList());

            int createdCount = 0;
            for (Map<String, Object> item : actionItems) {
                String content = (String) item.getOrDefault("content", "");
                String assigneeName = (String) item.getOrDefault("assignee", "");
                String priorityStr = (String) item.getOrDefault("priority", "MEDIUM");

                // 查找责任人
                User assignee = userRepo.findByUsername(assigneeName).orElse(null);
                if (assignee == null) {
                    // 用 displayName 匹配
                    List<User> allUsers = userRepo.findAll();
                    for (User u : allUsers) {
                        if (assigneeName.equals(u.getDisplayName())) {
                            assignee = u;
                            break;
                        }
                    }
                }

                ActionItem ai = new ActionItem();
                ai.setMeeting(meeting);
                ai.setContent(content);
                ai.setAssignee(assignee != null ? assignee : userRepo.findById(userId).orElse(null));
                ai.setAssigner(userRepo.findById(userId).orElse(null));
                ai.setTeam(meeting.getTeam());
                ai.setPriority(ActionItem.Priority.valueOf(priorityStr.toUpperCase()));
                ai.setStatus(ActionItem.ActionItemStatus.PENDING);
                repo.save(ai);
                createdCount++;
            }

            Map<String, Object> result = new HashMap<>();
            result.put("message", "成功生成 " + createdCount + " 条待办");
            result.put("count", createdCount);
            return ApiResponse.ok(result);
        } catch (Exception e) {
            return ApiResponse.error(500, "AI 结果解析失败: " + e.getMessage());
        }
    }

    private void updateCompletedAt(ActionItem item, ActionItem.ActionItemStatus oldStatus,
                                    ActionItem.ActionItemStatus newStatus) {
        if (newStatus == ActionItem.ActionItemStatus.DONE && oldStatus != ActionItem.ActionItemStatus.DONE) {
            item.setCompletedAt(LocalDateTime.now());
        } else if (newStatus != ActionItem.ActionItemStatus.DONE && oldStatus == ActionItem.ActionItemStatus.DONE) {
            item.setCompletedAt(null);
        }
    }
}
