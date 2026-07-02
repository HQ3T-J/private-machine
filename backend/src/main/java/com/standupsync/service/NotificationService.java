package com.standupsync.service;

import com.standupsync.model.Notification;
import com.standupsync.model.Notification.NotificationType;
import com.standupsync.repository.NotificationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class NotificationService {

    private final NotificationRepository notificationRepository;

    public NotificationService(NotificationRepository notificationRepository) {
        this.notificationRepository = notificationRepository;
    }

    // ═══════════════════════════════════════════════
    //  创建
    // ═══════════════════════════════════════════════

    /**
     * 创建一条通知。
     */
    @Transactional
    public Notification createNotification(String userId, Long teamId, NotificationType type,
                                           String content, Long relatedItemId, String senderId) {
        Notification notification = new Notification();
        notification.setUserId(userId);
        notification.setTeamId(teamId);
        notification.setType(type);
        notification.setContent(content);
        notification.setRelatedItemId(relatedItemId);
        notification.setSenderId(senderId);
        notification.setIsRead(false);
        return notificationRepository.save(notification);
    }

    // ═══════════════════════════════════════════════
    //  查询
    // ═══════════════════════════════════════════════

    /**
     * 获取用户未读通知列表（按创建时间倒序）。
     */
    public List<Notification> getUnread(String userId) {
        return notificationRepository.findByUserIdAndIsReadFalseOrderByCreatedAtDesc(userId);
    }

    /**
     * 获取用户所有通知列表（按创建时间倒序）。
     */
    public List<Notification> getAll(String userId) {
        return notificationRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    /**
     * 获取用户未读通知数量。
     */
    public long getUnreadCount(String userId) {
        return notificationRepository.countByUserIdAndIsReadFalse(userId);
    }

    /**
     * 获取通知统计信息。
     */
    public Map<String, Object> getStats(String userId) {
        long unreadCount = getUnreadCount(userId);
        Map<String, Object> stats = new HashMap<>();
        stats.put("unreadCount", unreadCount);
        return stats;
    }

    // ═══════════════════════════════════════════════
    //  已读操作
    // ═══════════════════════════════════════════════

    /**
     * 标记单条通知为已读。
     */
    @Transactional
    public Notification markAsRead(Long id) {
        Notification notification = notificationRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("通知不存在: " + id));
        notification.setIsRead(true);
        return notificationRepository.save(notification);
    }

    /**
     * 标记用户所有通知为已读。
     */
    @Transactional
    public void markAllAsRead(String userId) {
        List<Notification> unread = notificationRepository
                .findByUserIdAndIsReadFalseOrderByCreatedAtDesc(userId);
        for (Notification n : unread) {
            n.setIsRead(true);
        }
        notificationRepository.saveAll(unread);
    }

    /**
     * 将与某个待办事项相关的所有未读通知标记为已读。
     */
    @Transactional
    public void markAsReadByRelatedItemId(Long relatedItemId) {
        List<Notification> notifications = notificationRepository
                .findByRelatedItemIdAndIsReadFalse(relatedItemId);
        for (Notification n : notifications) {
            n.setIsRead(true);
        }
        notificationRepository.saveAll(notifications);
    }

    // ═══════════════════════════════════════════════
    //  删除
    // ═══════════════════════════════════════════════

    /**
     * 删除单条通知。
     */
    @Transactional
    public void delete(Long id) {
        if (!notificationRepository.existsById(id)) {
            throw new IllegalArgumentException("通知不存在: " + id);
        }
        notificationRepository.deleteById(id);
    }
}
