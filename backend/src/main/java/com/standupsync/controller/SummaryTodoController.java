package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.model.ActionItem;
import com.standupsync.model.Meeting;
import com.standupsync.model.TeamMember;
import com.standupsync.repository.ActionItemRepository;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.repository.UserRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * 从站会纪要自动生成待办 — 无需用户输入，直接解析AI纪要
 */
@RestController
@RequestMapping("/api")
public class SummaryTodoController {

    private final MeetingRepository meetingRepo;
    private final ActionItemRepository actionItemRepo;
    private final TeamMemberRepository teamMemberRepo;
    private final UserRepository userRepo;
    private final ObjectMapper mapper = new ObjectMapper();

    public SummaryTodoController(MeetingRepository meetingRepo,
                                  ActionItemRepository actionItemRepo,
                                  TeamMemberRepository teamMemberRepo,
                                  UserRepository userRepo) {
        this.meetingRepo = meetingRepo;
        this.actionItemRepo = actionItemRepo;
        this.teamMemberRepo = teamMemberRepo;
        this.userRepo = userRepo;
    }

    /** 获取有AI纪要的站会列表 */
    @GetMapping("/meetings/with-summary")
    public ApiResponse<?> meetingsWithSummary(@RequestAttribute("userId") String userId,
                                               @RequestParam Long teamId) {
        List<Meeting> all = meetingRepo.findByTeamIdOrderByCreatedAtDesc(teamId);
        List<Map<String, Object>> result = new ArrayList<>();
        for (Meeting m : all) {
            if (m.getAiResult() != null && !m.getAiResult().isBlank()) {
                Map<String, Object> info = new LinkedHashMap<>();
                info.put("id", m.getId());
                info.put("title", m.getTitle());
                info.put("sprintNo", m.getSprintNo());
                info.put("createdAt", m.getCreatedAt());
                info.put("status", m.getStatus().name());
                result.add(info);
            }
        }
        return ApiResponse.ok(result);
    }

    /** 从指定站会的AI纪要自动生成待办 */
    @PostMapping("/action-items/ai-from-summary/{meetingId}")
    public ApiResponse<?> generateFromSummary(@RequestAttribute("userId") String userId,
                                               @PathVariable Long meetingId) {
        Meeting meeting = meetingRepo.findById(meetingId).orElse(null);
        if (meeting == null) return ApiResponse.error(404, "站会不存在");
        if (meeting.getAiResult() == null || meeting.getAiResult().isBlank())
            return ApiResponse.error(400, "该站会尚无AI纪要");

        try {
            Map<String, Object> aiResult = mapper.readValue(meeting.getAiResult(),
                    new com.fasterxml.jackson.core.type.TypeReference<Map<String, Object>>() {});

            List<String> blockers = castToList(aiResult.get("blockers"));
            List<String> planList = castToList(aiResult.get("planList"));

            // 从阻碍和计划中提取待办
            List<Map<String, String>> todoItems = new ArrayList<>();
            for (String blocker : blockers) {
                if (blocker != null && !blocker.isBlank()) {
                    todoItems.add(Map.of("content", "【阻碍】" + blocker, "priority", "HIGH"));
                }
            }
            for (String plan : planList) {
                if (plan != null && !plan.isBlank()) {
                    todoItems.add(Map.of("content", plan, "priority", "MEDIUM"));
                }
            }

            // 自动创建待办
            int created = 0;
            for (Map<String, String> item : todoItems) {
                ActionItem ai = new ActionItem();
                ai.setMeeting(meeting);
                ai.setContent(item.get("content"));
                ai.setPriority(ActionItem.Priority.valueOf(item.get("priority")));
                ai.setTeam(meeting.getTeam());
                ai.setStatus(ActionItem.ActionItemStatus.PENDING);
                userRepo.findById(userId).ifPresent(ai::setAssigner);
                userRepo.findById(userId).ifPresent(ai::setAssignee);
                actionItemRepo.save(ai);
                created++;
            }

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("created", created);
            result.put("total", todoItems.size());
            result.put("message", "已自动创建 " + created + " 条待办");
            return ApiResponse.ok(result);
        } catch (Exception e) {
            return ApiResponse.error(500, "纪要解析失败: " + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private List<String> castToList(Object obj) {
        if (obj instanceof List) return (List<String>) obj;
        return Collections.emptyList();
    }
}
