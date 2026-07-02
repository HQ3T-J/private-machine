package com.standup.todo.repository;

import com.standup.todo.entity.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface NotificationRepository extends JpaRepository<Notification, Long> {

    List<Notification> findByUserIdAndIsReadFalseOrderByCreatedAtDesc(String userId);

    long countByUserIdAndIsReadFalse(String userId);

    List<Notification> findByUserIdOrderByCreatedAtDesc(String userId);

    List<Notification> findByRelatedTodoIdAndIsReadFalse(Long relatedTodoId);
}
