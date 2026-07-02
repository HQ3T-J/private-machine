package com.standupsync.controller;

import com.standupsync.dto.AIGenerateRequest;
import com.standupsync.dto.ApiResponse;
import com.standupsync.service.TodoAIService;
import com.standupsync.service.TodoAIService.ParsedTodo;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
public class TodoAIController {

    private final TodoAIService aiService;

    public TodoAIController(TodoAIService aiService) {
        this.aiService = aiService;
    }

    @PostMapping("/action-items/ai-generate")
    public ApiResponse<List<ParsedTodo>> aiGenerate(
            @RequestAttribute("userId") String userId,
            @RequestBody AIGenerateRequest req) {
        try {
            List<ParsedTodo> todos = aiService.generateTodos(req.getContent(), req.getTeamId());
            return ApiResponse.ok(todos);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }
}
