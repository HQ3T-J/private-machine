package com.standupsync.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.standupsync.dto.Result;
import com.standupsync.dto.TodoCreateDTO;
import com.standupsync.entity.*;
import com.standupsync.mapper.*;
import com.standupsync.websocket.StandupWebSocketHandler;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class TodoService {

    private final TodoItemMapper todoMapper;
    private final StandupActionItemMapper actionItemMapper;
    private final StandupWebSocketHandler wsHandler;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public TodoService(TodoItemMapper todoMapper, StandupActionItemMapper actionItemMapper,
                       StandupWebSocketHandler wsHandler) {
        this.todoMapper = todoMapper;
        this.actionItemMapper = actionItemMapper;
        this.wsHandler = wsHandler;
    }

    private void broadcastTeam(Long teamId, String type, Object payload) {
        try {
            Map<String, Object> msg = new HashMap<>();
            msg.put("type", type);
            msg.put("payload", payload);
            wsHandler.broadcast(String.valueOf(teamId), objectMapper.writeValueAsString(msg));
        } catch (Exception ignored) {}
    }

    private Map<String, Object> _m(Object... kv) {
        Map<String, Object> m = new HashMap<>();
        for (int i = 0; i < kv.length; i += 2) {
            m.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return m;
    }

    public Result<?> getTodos(Long teamId, Long userId) {
        List<TodoItem> todos = todoMapper.findByTeam(teamId);
        return Result.ok(todos);
    }

    @Transactional
    public Result<?> createTodo(TodoCreateDTO dto, Long assignerId) {
        TodoItem todo = new TodoItem();
        todo.setTeamId(dto.getTeamId());
        todo.setContent(dto.getContent());
        todo.setAssigneeId(dto.getAssigneeId());
        todo.setAssignerId(assignerId);
        todo.setPriority(dto.getPriority() != null ? dto.getPriority() : "medium");
        todo.setStatus("pending");
        todo.setDeadline(dto.getDeadline());
        todo.setSourceStandupId(dto.getSourceStandupId());
        todoMapper.insert(todo);
        broadcastTeam(dto.getTeamId(), "todo:created", todo);
        return Result.ok("待办已创建", todo);
    }

    public Result<?> updateStatus(Long todoId, String status, Long userId) {
        TodoItem todo = todoMapper.selectById(todoId);
        if (todo == null) return Result.fail("待办不存在");
        todo.setStatus(status);
        if ("done".equals(status)) todo.setCompletedAt(LocalDateTime.now());
        todoMapper.updateById(todo);
        broadcastTeam(todo.getTeamId(), "todo:updated", _m("id", todoId, "status", status));
        return Result.ok("状态已更新");
    }

    public Result<?> getUnfinishedTodos(Long userId) {
        List<TodoItem> list = todoMapper.findUnfinishedByUser(userId);
        return Result.ok(list);
    }

    @Transactional
    public Result<?> generateFromActionItems(Long standupId) {
        List<StandupActionItem> items = actionItemMapper.selectList(
                new LambdaQueryWrapper<StandupActionItem>().eq(StandupActionItem::getStandupId, standupId)
                        .eq(StandupActionItem::getIsTodoGenerated, 0));
        int count = 0;
        for (StandupActionItem item : items) {
            TodoItem todo = new TodoItem();
            // Get teamId from standup meeting
            todo.setTeamId(1L); // Simplified
            todo.setContent(item.getContent());
            todo.setAssigneeId(item.getAssigneeId());
            todo.setPriority(item.getPriority());
            todo.setStatus("pending");
            todo.setDeadline(item.getDeadline());
            todo.setSourceStandupId(standupId);
            todoMapper.insert(todo);
            item.setIsTodoGenerated(1);
            item.setTodoId(todo.getId());
            actionItemMapper.updateById(item);
            count++;
        }
        return Result.ok("已生成 " + count + " 个待办");
    }

    // Scheduled task: mark overdue todos every 5 minutes
    @Scheduled(fixedRate = 300000)
    public void markOverdueTodos() {
        int count = todoMapper.markOverdue();
        if (count > 0) System.out.println("Marked " + count + " todos as overdue");
    }
}
