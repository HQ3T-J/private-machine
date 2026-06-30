package com.standupsync.repository;

import com.standupsync.model.ActionItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ActionItemRepository extends JpaRepository<ActionItem, Long> {

    List<ActionItem> findByMeetingId(Long meetingId);

    List<ActionItem> findByAssigneeId(String assigneeId);

    List<ActionItem> findByTeamId(Long teamId);

    List<ActionItem> findByTeamIdAndStatus(Long teamId, ActionItem.ActionItemStatus status);
}
