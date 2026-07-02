package com.standupsync.service;

import com.standupsync.model.ActionItem;
import com.standupsync.model.ActionItem.ActionItemStatus;
import com.standupsync.model.ActionItem.TransferStatus;
import com.standupsync.model.Notification.NotificationType;
import com.standupsync.model.TeamMember;
import com.standupsync.model.TeamMember.MemberRole;
import com.standupsync.model.User;
import com.standupsync.repository.ActionItemRepository;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class TodoTransferService {

    private final ActionItemRepository actionItemRepository;
    private final UserRepository userRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final NotificationService notificationService;

    public TodoTransferService(ActionItemRepository actionItemRepository,
                               UserRepository userRepository,
                               TeamMemberRepository teamMemberRepository,
                               NotificationService notificationService) {
        this.actionItemRepository = actionItemRepository;
        this.userRepository = userRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.notificationService = notificationService;
    }

    // ═══════════════════════════════════════════════
    //  核心转交方法
    // ═══════════════════════════════════════════════

    /**
     * 发起转交。非管理员需要审批，管理员直接通过。
     */
    @Transactional
    public ActionItem transferTodo(Long todoId, String targetUserId, String reason, String userId) {
        ActionItem todo = actionItemRepository.findById(todoId)
                .orElseThrow(() -> new IllegalArgumentException("待办事项不存在: " + todoId));

        if (!canOperate(todo, userId)) {
            throw new IllegalArgumentException("无权操作该待办事项");
        }

        User targetUser = userRepository.findById(targetUserId)
                .orElseThrow(() -> new IllegalArgumentException("目标用户不存在: " + targetUserId));

        Long teamId = todo.getTeam().getId();

        if (isAdmin(userId, teamId)) {
            // ── 管理员直接转交 ──
            String originalId = todo.getAssignee() != null ? todo.getAssignee().getId() : null;
            todo.setOriginalAssigneeId(originalId);
            todo.setAssignee(targetUser);
            todo.setTransferStatus(TransferStatus.APPROVED);
            todo.setTransferReason(reason);
            todo.setTransferredBy(userId);
            todo.setTransferApprovedBy(userId);
            todo.setTransferApprovedAt(LocalDateTime.now());

            actionItemRepository.save(todo);

            // 通知新负责人
            String notifContent = "管理员已将待办事项【" + todo.getContent() + "】转交给你";
            notificationService.createNotification(
                    targetUserId, teamId, NotificationType.TODO_ASSIGNED,
                    notifContent, todo.getId(), userId);

        } else {
            // ── 非管理员：进入审批流 ──
            String originalId = todo.getAssignee() != null ? todo.getAssignee().getId() : null;
            todo.setOriginalAssigneeId(originalId);
            todo.setPendingAssigneeId(targetUserId);
            todo.setTransferStatus(TransferStatus.PENDING);
            todo.setTransferReason(reason);
            todo.setTransferredBy(userId);
            todo.setStatus(ActionItemStatus.REVIEWING);

            actionItemRepository.save(todo);

            // 通知所有管理员
            String notifContent = "用户【" + userId + "】请求将待办事项【" + todo.getContent()
                    + "】转交给【" + targetUserId + "】，原因：" + (reason != null ? reason : "无");
            List<TeamMember> admins = teamMemberRepository.findByTeamId(teamId).stream()
                    .filter(m -> m.getRole() == MemberRole.TECH_LEAD || m.getRole() == MemberRole.SCRUM_MASTER)
                    .collect(Collectors.toList());
            for (TeamMember admin : admins) {
                notificationService.createNotification(
                        admin.getUserId(), teamId, NotificationType.TODO_TRANSFERRED,
                        notifContent, todo.getId(), userId);
            }
        }

        return todo;
    }

    /**
     * 管理员审批通过转交。
     */
    @Transactional
    public ActionItem approveTransfer(Long todoId, String userId) {
        ActionItem todo = actionItemRepository.findById(todoId)
                .orElseThrow(() -> new IllegalArgumentException("待办事项不存在: " + todoId));

        Long teamId = todo.getTeam().getId();
        if (!isAdmin(userId, teamId)) {
            throw new IllegalArgumentException("只有管理员可以审批转交");
        }

        if (todo.getTransferStatus() != TransferStatus.PENDING) {
            throw new IllegalArgumentException("该待办事项不在待审批状态");
        }

        String pendingAssigneeId = todo.getPendingAssigneeId();
        if (pendingAssigneeId == null) {
            throw new IllegalArgumentException("待审批转交缺少目标责任人");
        }

        User newAssignee = userRepository.findById(pendingAssigneeId)
                .orElseThrow(() -> new IllegalArgumentException("目标用户不存在: " + pendingAssigneeId));

        todo.setAssignee(newAssignee);
        todo.setTransferStatus(TransferStatus.APPROVED);
        todo.setTransferApprovedBy(userId);
        todo.setTransferApprovedAt(LocalDateTime.now());
        todo.setStatus(ActionItemStatus.PENDING);

        actionItemRepository.save(todo);

        // 通知新负责人
        String newNotif = "管理员已通过转交审批，待办事项【" + todo.getContent() + "】现已分配给你";
        notificationService.createNotification(
                pendingAssigneeId, teamId, NotificationType.TODO_ASSIGNED,
                newNotif, todo.getId(), userId);

        // 通知原负责人审批通过
        String originalId = todo.getOriginalAssigneeId();
        if (originalId != null) {
            String origNotif = "管理员已通过待办事项【" + todo.getContent() + "】的转交审批";
            notificationService.createNotification(
                    originalId, teamId, NotificationType.TRANSFER_APPROVED,
                    origNotif, todo.getId(), userId);
        }

        return todo;
    }

    /**
     * 管理员驳回转交。
     */
    @Transactional
    public ActionItem rejectTransfer(Long todoId, String userId, String reason) {
        ActionItem todo = actionItemRepository.findById(todoId)
                .orElseThrow(() -> new IllegalArgumentException("待办事项不存在: " + todoId));

        Long teamId = todo.getTeam().getId();
        if (!isAdmin(userId, teamId)) {
            throw new IllegalArgumentException("只有管理员可以驳回转交");
        }

        todo.setTransferStatus(TransferStatus.REJECTED);
        todo.setRejectReason(reason);
        todo.setStatus(ActionItemStatus.PENDING);

        actionItemRepository.save(todo);

        // 通知原负责人已被驳回
        String originalId = todo.getOriginalAssigneeId();
        if (originalId != null) {
            String notifContent = "管理员已驳回待办事项【" + todo.getContent()
                    + "】的转交请求，原因：" + (reason != null ? reason : "无");
            notificationService.createNotification(
                    originalId, teamId, NotificationType.TRANSFER_REJECTED,
                    notifContent, todo.getId(), userId);
        }

        return todo;
    }

    /**
     * 发起人取消转交。
     */
    @Transactional
    public ActionItem cancelTransfer(Long todoId, String userId) {
        ActionItem todo = actionItemRepository.findById(todoId)
                .orElseThrow(() -> new IllegalArgumentException("待办事项不存在: " + todoId));

        if (todo.getTransferredBy() == null || !todo.getTransferredBy().equals(userId)) {
            throw new IllegalArgumentException("只有转交发起人可以取消转交");
        }

        todo.setTransferStatus(TransferStatus.NONE);
        todo.setStatus(ActionItemStatus.PENDING);

        actionItemRepository.save(todo);

        // 标记相关通知为已读
        notificationService.markAsReadByRelatedItemId(todoId);

        return todo;
    }

    // ═══════════════════════════════════════════════
    //  查询方法
    // ═══════════════════════════════════════════════

    /**
     * 获取待审批转交列表（管理员）。
     */
    public List<ActionItem> getPendingTransfers(Long teamId, String userId) {
        if (!isAdmin(userId, teamId)) {
            throw new IllegalArgumentException("只有管理员可以查看待审批转交");
        }
        List<ActionItem> allItems = actionItemRepository.findByTeamId(teamId);
        return allItems.stream()
                .filter(item -> item.getTransferStatus() == TransferStatus.PENDING)
                .collect(Collectors.toList());
    }

    /**
     * 获取已审批/已驳回转交列表（管理员）。
     */
    public List<ActionItem> getReviewedTransfers(Long teamId, String userId) {
        if (!isAdmin(userId, teamId)) {
            throw new IllegalArgumentException("只有管理员可以查看已处理转交");
        }
        List<ActionItem> allItems = actionItemRepository.findByTeamId(teamId);
        return allItems.stream()
                .filter(item -> item.getTransferStatus() == TransferStatus.APPROVED
                        || item.getTransferStatus() == TransferStatus.REJECTED)
                .filter(item -> item.getTransferRecordHidden() == null
                        || !item.getTransferRecordHidden())
                .collect(Collectors.toList());
    }

    /**
     * 隐藏转交记录（管理员）。
     */
    @Transactional
    public ActionItem hideTransferRecord(Long todoId, String userId) {
        ActionItem todo = actionItemRepository.findById(todoId)
                .orElseThrow(() -> new IllegalArgumentException("待办事项不存在: " + todoId));

        Long teamId = todo.getTeam().getId();
        if (!isAdmin(userId, teamId)) {
            throw new IllegalArgumentException("只有管理员可以隐藏转交记录");
        }

        todo.setTransferRecordHidden(true);
        return actionItemRepository.save(todo);
    }

    // ═══════════════════════════════════════════════
    //  辅助方法
    // ═══════════════════════════════════════════════

    /**
     * 判断用户是否是团队管理员（TECH_LEAD 或 SCRUM_MASTER）。
     */
    private boolean isAdmin(String userId, Long teamId) {
        Optional<TeamMember> memberOpt = teamMemberRepository.findByTeamIdAndUserId(teamId, userId);
        if (memberOpt.isEmpty()) {
            return false;
        }
        MemberRole role = memberOpt.get().getRole();
        return role == MemberRole.TECH_LEAD || role == MemberRole.SCRUM_MASTER;
    }

    /**
     * 判断用户是否可以操作待办事项：管理员 或 当前负责人。
     */
    private boolean canOperate(ActionItem item, String userId) {
        if (isAdmin(userId, item.getTeam().getId())) {
            return true;
        }
        return item.getAssignee() != null && userId.equals(item.getAssignee().getId());
    }
}
