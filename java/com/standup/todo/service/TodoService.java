package com.standup.todo.service;

import com.standup.todo.dto.TodoRequest;
import com.standup.todo.dto.TodoResponse;
import com.standup.todo.entity.Notification;
import com.standup.todo.entity.TeamMember;
import com.standup.todo.entity.Todo;
import com.standup.todo.repository.TeamMemberRepository;
import com.standup.todo.repository.TodoRepository;
import com.standup.todo.repository.TeamMemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TodoService {

    private final TodoRepository todoRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final NotificationService notificationService;

    public TodoResponse createTodo(TodoRequest request, String userId) {
        String assigneeId = request.getAssigneeId() != null ? request.getAssigneeId() : userId;

        if (!isAdmin(userId, request.getTeamId()) && !userId.equals(assigneeId)) {
            throw new RuntimeException("普通用户只能为自己创建待办");
        }

        // 验证截止日期不能早于当前时间
        if (request.getDueDate() != null && request.getDueDate().isBefore(LocalDateTime.now())) {
            throw new RuntimeException("截止日期不能早于当前时间");
        }

        Todo todo = new Todo();
        todo.setContent(request.getContent());
        todo.setAssigneeId(assigneeId);
        todo.setCreatorId(userId);
        todo.setDueDate(request.getDueDate());
        todo.setPriority(Todo.Priority.valueOf(request.getPriority()));
        todo.setTeamId(request.getTeamId());

        Todo savedTodo = todoRepository.save(todo);

        // 发送通知给责任人（如果指派给其他人）
        if (!userId.equals(assigneeId)) {
            String content = String.format("你有一个新的待办任务：%s", request.getContent());
            notificationService.createNotification(
                assigneeId, request.getTeamId(),
                Notification.NotificationType.TODO_ASSIGNED,
                content, savedTodo.getId(), userId
            );
        }

        return convertToResponse(savedTodo, userId);
    }

    public List<TodoResponse> getTodoList(String teamId, String userId, String status) {
        List<Todo> todos;
        if (isAdmin(userId, teamId)) {
            todos = todoRepository.findByTeamIdAndIsDeletedFalse(teamId);
        } else {
            todos = todoRepository.findByAssigneeIdAndIsDeletedFalse(userId);
        }

        if (status != null && !status.equals("ALL")) {
            Todo.Status todoStatus = Todo.Status.valueOf(status);
            todos = todos.stream()
                    .filter(t -> t.getStatus() == todoStatus)
                    .collect(Collectors.toList());
        }

        return todos.stream()
                .map(t -> convertToResponse(t, userId))
                .collect(Collectors.toList());
    }

    public TodoResponse updateStatus(Long todoId, String newStatus, String userId) {
        Todo todo = todoRepository.findById(todoId)
                .orElseThrow(() -> new RuntimeException("待办不存在"));

        if (!canOperate(todo, userId)) {
            throw new RuntimeException("无权限操作此待办");
        }

        todo.setStatus(Todo.Status.valueOf(newStatus));
        if (newStatus.equals("COMPLETED")) {
            todo.setCompletedAt(LocalDateTime.now());
        }

        return convertToResponse(todoRepository.save(todo), userId);
    }

    public void deleteTodo(Long todoId, String userId) {
        Todo todo = todoRepository.findById(todoId)
                .orElseThrow(() -> new RuntimeException("待办不存在"));

        if (!isAdmin(userId, todo.getTeamId())) {
            throw new RuntimeException("仅管理员可以删除待办");
        }

        todo.setIsDeleted(true);
        todoRepository.save(todo);
    }

    public TodoResponse transferTodo(Long todoId, String targetUserId, String reason, String userId) {
        Todo todo = todoRepository.findById(todoId)
                .orElseThrow(() -> new RuntimeException("待办不存在"));

        // 权限校验：管理员可转交任何人，普通用户只能转交自己的
        if (!canOperate(todo, userId)) {
            throw new RuntimeException("无权限转交此待办");
        }

        todo.setTransferReason(reason);
        todo.setTransferredBy(userId);
        todo.setOriginalAssigneeId(todo.getAssigneeId()); // 保存原始责任人

        // 管理员转交直接生效，普通用户转交需要审核
        if (isAdmin(userId, todo.getTeamId())) {
            todo.setAssigneeId(targetUserId);
            todo.setTransferStatus(Todo.TransferStatus.APPROVED);
            todo.setTransferApprovedBy(userId);
            todo.setTransferApprovedAt(LocalDateTime.now());

            // 发送通知给新的责任人
            String content = String.format("你有一个待办任务被转交：%s", todo.getContent());
            notificationService.createNotification(
                targetUserId, todo.getTeamId(),
                Notification.NotificationType.TODO_TRANSFERRED,
                content, todo.getId(), userId
            );
        } else {
            // 普通用户转交，保存目标用户到pendingAssigneeId，设置状态为审核中
            todo.setPendingAssigneeId(targetUserId);
            todo.setTransferStatus(Todo.TransferStatus.PENDING);
            todo.setStatus(Todo.Status.REVIEWING);

            // 发送通知给所有管理员
            List<TeamMember> admins = teamMemberRepository.findByTeamId(todo.getTeamId())
                    .stream()
                    .filter(TeamMember::isAdmin)
                    .collect(Collectors.toList());

            for (TeamMember admin : admins) {
                String content = String.format("有新的转交申请：%s（原责任人：%s → 新责任人：%s）",
                        todo.getContent(), todo.getAssigneeId(), targetUserId);
                notificationService.createNotification(
                    admin.getUserId(), todo.getTeamId(),
                    Notification.NotificationType.TODO_TRANSFERRED,
                    content, todo.getId(), userId
                );
            }
        }

        return convertToResponse(todoRepository.save(todo), userId);
    }

    public TodoResponse approveTransfer(Long todoId, String userId) {
        Todo todo = todoRepository.findById(todoId)
                .orElseThrow(() -> new RuntimeException("待办不存在"));

        if (!isAdmin(userId, todo.getTeamId())) {
            throw new RuntimeException("仅管理员可以审核转交");
        }

        if (todo.getTransferStatus() != Todo.TransferStatus.PENDING) {
            throw new RuntimeException("该待办没有待审核的转交请求");
        }

        // 批准转交
        String oldAssigneeId = todo.getOriginalAssigneeId() != null ? todo.getOriginalAssigneeId() : todo.getAssigneeId();
        todo.setAssigneeId(todo.getPendingAssigneeId());
        todo.setPendingAssigneeId(null);
        todo.setTransferStatus(Todo.TransferStatus.APPROVED);
        todo.setTransferApprovedBy(userId);
        todo.setTransferApprovedAt(LocalDateTime.now());
        todo.setStatus(Todo.Status.PENDING); // 恢复为待处理状态

        // 发送通知给新的责任人
        String content = String.format("你有一个待办任务：%s", todo.getContent());
        notificationService.createNotification(
            todo.getAssigneeId(), todo.getTeamId(),
            Notification.NotificationType.TODO_ASSIGNED,
            content, todo.getId(), userId
        );

        // 发送通知给原负责人
        String oldContent = String.format("你的待办转交申请已批准：%s", todo.getContent());
        notificationService.createNotification(
            oldAssigneeId, todo.getTeamId(),
            Notification.NotificationType.TRANSFER_APPROVED,
            oldContent, todo.getId(), userId
        );

        // 自动标记管理员的转交申请通知为已读（不标记新责任人和原责任人的通知）
        // 注意：这里不应该调用markAsReadByRelatedTodoId，因为它会标记所有相关通知为已读

        return convertToResponse(todoRepository.save(todo), userId);
    }

    public TodoResponse rejectTransfer(Long todoId, String userId, String rejectReason) {
        Todo todo = todoRepository.findById(todoId)
                .orElseThrow(() -> new RuntimeException("待办不存在"));

        if (!isAdmin(userId, todo.getTeamId())) {
            throw new RuntimeException("仅管理员可以审核转交");
        }

        if (todo.getTransferStatus() != Todo.TransferStatus.PENDING) {
            throw new RuntimeException("该待办没有待审核的转交请求");
        }

        // 拒绝转交
        String originalAssigneeId = todo.getOriginalAssigneeId() != null ? todo.getOriginalAssigneeId() : todo.getAssigneeId();
        // 保留pendingAssigneeId以便在审核记录中显示
        todo.setTransferStatus(Todo.TransferStatus.REJECTED);
        todo.setTransferApprovedBy(userId);
        todo.setTransferApprovedAt(LocalDateTime.now());
        todo.setStatus(Todo.Status.PENDING); // 恢复为待处理状态
        if (rejectReason != null && !rejectReason.trim().isEmpty()) {
            todo.setRejectReason(rejectReason);
        }

        // 发送通知给原负责人（转交申请人）
        String content = String.format("你的待办转交申请被拒绝：%s%s",
            todo.getContent(),
            (rejectReason != null && !rejectReason.trim().isEmpty()) ? "。拒绝理由: " + rejectReason : "");
        notificationService.createNotification(
            originalAssigneeId, todo.getTeamId(),
            Notification.NotificationType.TRANSFER_REJECTED,
            content, todo.getId(), userId
        );

        // 注意：这里不应该调用markAsReadByRelatedTodoId，因为它会标记所有相关通知为已读

        return convertToResponse(todoRepository.save(todo), userId);
    }

    public TodoResponse cancelTransfer(Long todoId, String userId) {
        Todo todo = todoRepository.findById(todoId)
                .orElseThrow(() -> new RuntimeException("待办不存在"));

        // 权限校验：只能取消自己发起的转交申请
        if (!userId.equals(todo.getTransferredBy())) {
            throw new RuntimeException("只能取消自己发起的转交申请");
        }

        if (todo.getTransferStatus() != Todo.TransferStatus.PENDING) {
            throw new RuntimeException("该待办没有待审核的转交请求");
        }

        // 取消转交
        todo.setPendingAssigneeId(null);
        todo.setTransferStatus(Todo.TransferStatus.NONE);
        todo.setStatus(Todo.Status.PENDING); // 恢复为待处理状态

        // 自动标记相关通知为已读
        notificationService.markAsReadByRelatedTodoId(todoId);

        return convertToResponse(todoRepository.save(todo), userId);
    }

    public List<TodoResponse> getPendingTransfers(String teamId, String userId) {
        if (!isAdmin(userId, teamId)) {
            throw new RuntimeException("仅管理员可以查看待审核转交");
        }

        return todoRepository.findByTeamIdAndTransferStatusAndIsDeletedFalse(teamId, Todo.TransferStatus.PENDING)
                .stream()
                .map(t -> convertToResponse(t, userId))
                .collect(Collectors.toList());
    }

    public List<TodoResponse> getReviewedTransfers(String teamId, String userId) {
        if (!isAdmin(userId, teamId)) {
            throw new RuntimeException("仅管理员可以查看已审核转交");
        }

        List<Todo.TransferStatus> reviewedStatuses = List.of(
            Todo.TransferStatus.APPROVED,
            Todo.TransferStatus.REJECTED
        );

        List<Todo> todos = todoRepository.findByTeamIdAndTransferStatusInAndIsDeletedFalse(teamId, reviewedStatuses);
        System.out.println("=== DEBUG: getReviewedTransfers ===");
        System.out.println("Team ID: " + teamId);
        System.out.println("Total todos found: " + todos.size());
        for (Todo t : todos) {
            System.out.println("Todo ID: " + t.getId() + ", Status: " + t.getTransferStatus() + ", Hidden: " + t.getTransferRecordHidden());
        }

        return todos.stream()
                .filter(t -> !t.getTransferRecordHidden()) // 过滤掉被隐藏的记录
                .map(t -> convertToResponse(t, userId))
                .collect(Collectors.toList());
    }

    public void hideTransferRecord(Long todoId, String userId) {
        Todo todo = todoRepository.findById(todoId)
                .orElseThrow(() -> new RuntimeException("待办不存在"));

        if (!isAdmin(userId, todo.getTeamId())) {
            throw new RuntimeException("仅管理员可以隐藏转交记录");
        }

        todo.setTransferRecordHidden(true);
        todoRepository.save(todo);
    }

    public List<TodoResponse> getDueSoonTodos(String teamId, String userId) {
        List<Todo> todos;
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime oneHourLater = now.plusHours(1);

        if (isAdmin(userId, teamId)) {
            todos = todoRepository.findByTeamIdAndIsDeletedFalse(teamId);
        } else {
            todos = todoRepository.findByAssigneeIdAndIsDeletedFalse(userId);
        }

        return todos.stream()
                .filter(t -> t.getDueDate() != null
                        && t.getDueDate().isAfter(now)
                        && t.getDueDate().isBefore(oneHourLater)
                        && t.getStatus() != Todo.Status.COMPLETED)
                .map(t -> convertToResponse(t, userId))
                .collect(Collectors.toList());
    }

    public List<TodoResponse> getOverdueTodos(String teamId, String userId) {
        List<Todo> todos;
        LocalDateTime now = LocalDateTime.now();

        if (isAdmin(userId, teamId)) {
            todos = todoRepository.findByTeamIdAndIsDeletedFalse(teamId);
        } else {
            todos = todoRepository.findByAssigneeIdAndIsDeletedFalse(userId);
        }

        return todos.stream()
                .filter(t -> t.getDueDate() != null
                        && t.getDueDate().isBefore(now)
                        && t.getStatus() != Todo.Status.COMPLETED)
                .map(t -> convertToResponse(t, userId))
                .collect(Collectors.toList());
    }

    public Map<String, Object> getStats(String teamId, String userId) {
        Map<String, Object> stats = new HashMap<>();
        long total, completed, inProgress, pending;

        if (isAdmin(userId, teamId)) {
            total = todoRepository.countByTeamIdAndIsDeletedFalse(teamId);
            completed = todoRepository.countByTeamIdAndStatusAndIsDeletedFalse(teamId, Todo.Status.COMPLETED);
            inProgress = todoRepository.countByTeamIdAndStatusAndIsDeletedFalse(teamId, Todo.Status.IN_PROGRESS);
            pending = todoRepository.countByTeamIdAndStatusAndIsDeletedFalse(teamId, Todo.Status.PENDING);
        } else {
            total = todoRepository.countByAssigneeIdAndIsDeletedFalse(userId);
            completed = todoRepository.countByAssigneeIdAndStatusAndIsDeletedFalse(userId, Todo.Status.COMPLETED);
            inProgress = todoRepository.countByAssigneeIdAndStatusAndIsDeletedFalse(userId, Todo.Status.IN_PROGRESS);
            pending = todoRepository.countByAssigneeIdAndStatusAndIsDeletedFalse(userId, Todo.Status.PENDING);
        }

        // 计算完成率
        double completionRate = total > 0 ? (double) completed / total * 100 : 0;

        stats.put("total", total);
        stats.put("completed", completed);
        stats.put("inProgress", inProgress);
        stats.put("pending", pending);
        stats.put("completionRate", Math.round(completionRate * 100.0) / 100.0);
        stats.put("isAdmin", isAdmin(userId, teamId));
        stats.put("scope", isAdmin(userId, teamId) ? "团队" : "个人");

        return stats;
    }

    private boolean isAdmin(String userId, String teamId) {
        return teamMemberRepository.existsByUserIdAndTeamIdAndRole(userId, teamId, TeamMember.Role.SCRUM_MASTER);
    }

    private boolean canOperate(Todo todo, String userId) {
        if (isAdmin(userId, todo.getTeamId())) {
            return true;
        }
        return userId.equals(todo.getAssigneeId());
    }

    private TodoResponse convertToResponse(Todo todo, String userId) {
        boolean isOverdue = todo.getDueDate() != null
                && todo.getDueDate().isBefore(LocalDateTime.now())
                && todo.getStatus() != Todo.Status.COMPLETED;

        boolean isDueSoon = todo.getDueDate() != null
                && todo.getDueDate().isAfter(LocalDateTime.now())
                && todo.getDueDate().isBefore(LocalDateTime.now().plusHours(1))
                && todo.getStatus() != Todo.Status.COMPLETED;

        return TodoResponse.builder()
                .id(todo.getId())
                .content(todo.getContent())
                .assigneeId(todo.getAssigneeId())
                .creatorId(todo.getCreatorId())
                .dueDate(todo.getDueDate())
                .priority(todo.getPriority().name())
                .status(todo.getStatus().name())
                .teamId(todo.getTeamId())
                .createdAt(todo.getCreatedAt())
                .completedAt(todo.getCompletedAt())
                .transferReason(todo.getTransferReason())
                .pendingAssigneeId(todo.getPendingAssigneeId())
                .originalAssigneeId(todo.getOriginalAssigneeId())
                .transferredBy(todo.getTransferredBy())
                .transferStatus(todo.getTransferStatus() != null ? todo.getTransferStatus().name() : null)
                .transferApprovedBy(todo.getTransferApprovedBy())
                .transferApprovedAt(todo.getTransferApprovedAt())
                .rejectReason(todo.getRejectReason())
                .isOverdue(isOverdue)
                .isDueSoon(isDueSoon)
                .hasPermission(canOperate(todo, userId))
                .pendingTransfer(todo.getTransferStatus() == Todo.TransferStatus.PENDING)
                .build();
    }
}
