package com.standupsync.repository;

import com.standupsync.model.MeetingSpeech;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MeetingSpeechRepository extends JpaRepository<MeetingSpeech, Long> {

    List<MeetingSpeech> findByMeetingIdOrderByCreatedAtAsc(Long meetingId);

    List<MeetingSpeech> findByMeetingIdAndSpeakerId(Long meetingId, String speakerId);
}
