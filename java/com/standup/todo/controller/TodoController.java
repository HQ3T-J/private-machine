package com.standup.todo.controller;

import com.standup.todo.dto.TodoRequest;
import com.standup.todo.dto.TodoResponse;
import com.standup.todo.dto.AIGenerateRequest;
import com.standup.todo.dto.AIGenerateResponse;
import com.standup.todo.entity.TeamMember;
import com.standup.todo.repository.TeamMemberRepository;
import com.standup.todo.service.TodoService;
import com.standup.todo.service.AIService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class TodoController {

    private final TodoService todoService;
    private final TeamMemberRepository teamMemberRepository;
    private final AIService aiService;

    @PostMapping("/todos")
    public ResponseEntity<TodoResponse> createTodo(
            @RequestBody TodoRequest request,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.createTodo(request, userId));
    }

    @GetMapping("/todos")
    public ResponseEntity<List<TodoResponse>> getTodoList(
            @RequestParam String teamId,
            @RequestHeader("X-User-Id") String userId,
            @RequestParam(required = false, defaultValue = "ALL") String status) {
        return ResponseEntity.ok(todoService.getTodoList(teamId, userId, status));
    }

    @PatchMapping("/todos/{id}/status")
    public ResponseEntity<TodoResponse> updateStatus(
            @PathVariable Long id,
            @RequestParam String status,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.updateStatus(id, status, userId));
    }

    @DeleteMapping("/todos/{id}")
    public ResponseEntity<Void> deleteTodo(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") String userId) {
        todoService.deleteTodo(id, userId);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/todos/{id}/transfer")
    public ResponseEntity<TodoResponse> transferTodo(
            @PathVariable Long id,
            @RequestParam String targetUserId,
            @RequestParam(required = false) String reason,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.transferTodo(id, targetUserId, reason, userId));
    }

    @PostMapping("/todos/{id}/approve-transfer")
    public ResponseEntity<TodoResponse> approveTransfer(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.approveTransfer(id, userId));
    }

    @PostMapping("/todos/{id}/reject-transfer")
    public ResponseEntity<TodoResponse> rejectTransfer(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") String userId,
            @RequestParam(required = false) String reason) {
        return ResponseEntity.ok(todoService.rejectTransfer(id, userId, reason));
    }

    @PostMapping("/todos/{id}/cancel-transfer")
    public ResponseEntity<TodoResponse> cancelTransfer(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.cancelTransfer(id, userId));
    }

    @GetMapping("/todos/reviewed-transfers")
    public ResponseEntity<List<TodoResponse>> getReviewedTransfers(
            @RequestParam String teamId,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.getReviewedTransfers(teamId, userId));
    }

    @PostMapping("/todos/{id}/hide-transfer-record")
    public ResponseEntity<Void> hideTransferRecord(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") String userId) {
        todoService.hideTransferRecord(id, userId);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/todos/pending-transfers")
    public ResponseEntity<List<TodoResponse>> getPendingTransfers(
            @RequestParam String teamId,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.getPendingTransfers(teamId, userId));
    }

    @GetMapping("/todos/stats")
    public ResponseEntity<Map<String, Object>> getStats(
            @RequestParam String teamId,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.getStats(teamId, userId));
    }

    @GetMapping("/todos/due-soon")
    public ResponseEntity<List<TodoResponse>> getDueSoonTodos(
            @RequestParam String teamId,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.getDueSoonTodos(teamId, userId));
    }

    @GetMapping("/todos/overdue")
    public ResponseEntity<List<TodoResponse>> getOverdueTodos(
            @RequestParam String teamId,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(todoService.getOverdueTodos(teamId, userId));
    }

    @GetMapping("/members")
    public ResponseEntity<List<Map<String, String>>> getMembers(@RequestParam String teamId) {
        List<TeamMember> members = teamMemberRepository.findByTeamId(teamId);
        List<Map<String, String>> result = members.stream()
                .map(m -> Map.of(
                        "userId", m.getUserId(),
                        "role", m.getRole().name()
                ))
                .collect(Collectors.toList());
        return ResponseEntity.ok(result);
    }

    @PostMapping("/todos/ai-generate")
    public ResponseEntity<AIGenerateResponse> aiGenerateTodos(
            @RequestBody AIGenerateRequest request,
            @RequestHeader("X-User-Id") String userId) {
        return ResponseEntity.ok(aiService.generateTodos(request.getContent(), request.getTeamId()));
    }
}
