package com.standupsync.repository;

import com.standupsync.model.MeetingParticipant;
import com.standupsync.model.MeetingParticipantId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MeetingParticipantRepository extends JpaRepository<MeetingParticipant, MeetingParticipantId> {

    List<MeetingParticipant> findByMeetingIdOrderBySpeechOrderAsc(Long meetingId);

    void deleteByMeetingIdAndUserId(Long meetingId, String userId);
}
