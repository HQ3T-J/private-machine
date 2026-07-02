package com.standupsync.repository;

import com.standupsync.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface NotificationRepository extends JpaRepository<Notification, Long> {

    List<Notification> findByUserIdAndIsReadFalseOrderByCreatedAtDesc(String userId);

    List<Notification> findByUserIdOrderByCreatedAtDesc(String userId);

    long countByUserIdAndIsReadFalse(String userId);

    List<Notification> findByRelatedItemIdAndIsReadFalse(Long relatedItemId);
}
