package com.standupsync.repository;

import com.standupsync.model.Meeting;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MeetingRepository extends JpaRepository<Meeting, Long> {

    List<Meeting> findByTeamIdOrderByCreatedAtDesc(Long teamId);

    Page<Meeting> findByTeamIdOrderByCreatedAtDesc(Long teamId, Pageable pageable);

    List<Meeting> findByTeamIdAndStatus(Long teamId, Meeting.MeetingStatus status);
}
