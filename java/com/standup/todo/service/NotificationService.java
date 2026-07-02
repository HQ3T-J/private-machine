package com.standup.todo.service;

import com.standup.todo.entity.Notification;
import com.standup.todo.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

@Service
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationRepository notificationRepository;

    public void createNotification(String userId, String teamId, Notification.NotificationType type,
                                   String content, Long relatedTodoId, String senderId) {
        Notification notification = new Notification();
        notification.setUserId(userId);
        notification.setTeamId(teamId);
        notification.setType(type);
        notification.setContent(content);
        notification.setRelatedTodoId(relatedTodoId);
        notification.setSenderId(senderId);
        notification.setIsRead(false);
        notificationRepository.save(notification);
    }

    public List<Notification> getUnreadNotifications(String userId) {
        return notificationRepository.findByUserIdAndIsReadFalseOrderByCreatedAtDesc(userId);
    }

    public long getUnreadCount(String userId) {
        return notificationRepository.countByUserIdAndIsReadFalse(userId);
    }

    public List<Notification> getAllNotifications(String userId) {
        return notificationRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    public void markAsRead(Long notificationId) {
        notificationRepository.findById(notificationId).ifPresent(notification -> {
            notification.setIsRead(true);
            notificationRepository.save(notification);
        });
    }

    public void markAllAsRead(String userId) {
        List<Notification> unreadNotifications = getUnreadNotifications(userId);
        unreadNotifications.forEach(notification -> {
            notification.setIsRead(true);
            notificationRepository.save(notification);
        });
    }

    public Map<String, Object> getNotificationStats(String userId) {
        Map<String, Object> stats = new HashMap<>();
        stats.put("unreadCount", getUnreadCount(userId));
        return stats;
    }

    public void deleteNotification(Long notificationId) {
        notificationRepository.deleteById(notificationId);
    }

    public void markAsReadByRelatedTodoId(Long relatedTodoId) {
        List<Notification> notifications = notificationRepository.findByRelatedTodoIdAndIsReadFalse(relatedTodoId);
        notifications.forEach(notification -> {
            notification.setIsRead(true);
            notificationRepository.save(notification);
        });
    }
}
