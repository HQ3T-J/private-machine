package com.standupsync.service;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.ActionItem;
import com.standupsync.model.Meeting;
import com.standupsync.model.Team;
import com.standupsync.model.User;
import com.standupsync.repository.ActionItemRepository;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.TeamRepository;
import com.standupsync.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class ActionItemService {

    private final ActionItemRepository repo;
    private final MeetingRepository meetingRepo;
    private final UserRepository userRepo;
    private final TeamRepository teamRepo;

    public ActionItemService(ActionItemRepository repo, MeetingRepository meetingRepo,
                             UserRepository userRepo, TeamRepository teamRepo) {
        this.repo = repo;
        this.meetingRepo = meetingRepo;
        this.userRepo = userRepo;
        this.teamRepo = teamRepo;
    }

    public ApiResponse<List<ActionItem>> listByUser(String userId, String status) {
        List<ActionItem> items = repo.findByAssigneeId(userId);
        if (status != null)
            items = items.stream().filter(i -> i.getStatus().name().equalsIgnoreCase(status)).toList();
        return ApiResponse.ok(items);
    }

    public ApiResponse<List<ActionItem>> unfinished(String userId) {
        List<ActionItem> items = repo.findByAssigneeId(userId);
        items = items.stream()
                .filter(i -> !"DONE".equalsIgnoreCase(i.getStatus().name())
                          && !"completed".equalsIgnoreCase(i.getStatus().name()))
                .toList();
        return ApiResponse.ok(items);
    }

    public ApiResponse<List<ActionItem>> listByTeam(Long teamId, String status) {
        if (status != null)
            return ApiResponse.ok(repo.findByTeamIdAndStatus(teamId,
                ActionItem.ActionItemStatus.valueOf(status.toUpperCase())));
        return ApiResponse.ok(repo.findByTeamId(teamId));
    }

    public ApiResponse<ActionItem> create(String userId, Map<String, Object> body) {
        ActionItem item = new ActionItem();
        item.setContent((String) body.get("content"));
        if (body.containsKey("assigneeId"))
            userRepo.findById((String) body.get("assigneeId")).ifPresent(item::setAssignee);
        else
            userRepo.findById(userId).ifPresent(item::setAssignee);
        userRepo.findById(userId).ifPresent(item::setAssigner);
        if (body.containsKey("teamId"))
            teamRepo.findById(Long.valueOf(body.get("teamId").toString())).ifPresent(item::setTeam);
        if (body.containsKey("meetingId"))
            meetingRepo.findById(Long.valueOf(body.get("meetingId").toString())).ifPresent(item::setMeeting);
        if (body.containsKey("status")) {
            ActionItem.ActionItemStatus old = item.getStatus();
            ActionItem.ActionItemStatus ns = ActionItem.ActionItemStatus.valueOf(
                ((String) body.get("status")).toUpperCase());
            item.setStatus(ns);
            updateCompletedAt(item, old, ns);
        }
        if (body.containsKey("priority"))
            item.setPriority(ActionItem.Priority.valueOf(((String) body.get("priority")).toUpperCase()));
        if (body.containsKey("confirmed"))
            item.setConfirmed(Boolean.valueOf(body.get("confirmed").toString()));
        return ApiResponse.ok(repo.save(item));
    }

    public ApiResponse<ActionItem> update(String userId, Long id, Map<String, Object> body) {
        ActionItem item = repo.findById(id).orElse(null);
        if (item == null) return ApiResponse.error(404, "待办不存在");
        if (body.containsKey("content")) item.setContent((String) body.get("content"));
        if (body.containsKey("status")) {
            ActionItem.ActionItemStatus old = item.getStatus();
            ActionItem.ActionItemStatus ns = ActionItem.ActionItemStatus.valueOf(
                ((String) body.get("status")).toUpperCase());
            item.setStatus(ns);
            updateCompletedAt(item, old, ns);
        }
        if (body.containsKey("priority"))
            item.setPriority(ActionItem.Priority.valueOf(((String) body.get("priority")).toUpperCase()));
        if (body.containsKey("assigneeId"))
            userRepo.findById((String) body.get("assigneeId")).ifPresent(item::setAssignee);
        if (body.containsKey("confirmed"))
            item.setConfirmed(Boolean.valueOf(body.get("confirmed").toString()));
        return ApiResponse.ok(repo.save(item));
    }

    public ApiResponse<Void> delete(String userId, Long id) {
        ActionItem item = repo.findById(id).orElse(null);
        if (item == null) return ApiResponse.error(404, "待办不存在");
        boolean isOwner = item.getAssigner() != null && item.getAssigner().getId().equals(userId);
        boolean isAssignee = item.getAssignee() != null && item.getAssignee().getId().equals(userId);
        if (!isOwner && !isAssignee) return ApiResponse.error(403, "无权删除此待办");
        repo.deleteById(id);
        return ApiResponse.ok("已删除", null);
    }

    public ApiResponse<Map<String, String>> updateStatus(String userId, Long itemId, String status) {
        ActionItem item = repo.findById(itemId).orElse(null);
        if (item == null) return ApiResponse.error(404, "待办不存在");
        if (!status.matches("pending|in_progress|reviewing|done|cancelled"))
            return ApiResponse.error(400, "无效状态: " + status);
        ActionItem.ActionItemStatus old = item.getStatus();
        ActionItem.ActionItemStatus ns = ActionItem.ActionItemStatus.valueOf(status.toUpperCase());
        item.setStatus(ns);
        updateCompletedAt(item, old, ns);
        repo.save(item);
        return ApiResponse.ok("状态已更新", Map.of("status", item.getStatus().name()));
    }

    private void updateCompletedAt(ActionItem item, ActionItem.ActionItemStatus old,
                                    ActionItem.ActionItemStatus ns) {
        if (ns == ActionItem.ActionItemStatus.DONE && old != ActionItem.ActionItemStatus.DONE)
            item.setCompletedAt(LocalDateTime.now());
        else if (ns != ActionItem.ActionItemStatus.DONE && old == ActionItem.ActionItemStatus.DONE)
            item.setCompletedAt(null);
    }
}
