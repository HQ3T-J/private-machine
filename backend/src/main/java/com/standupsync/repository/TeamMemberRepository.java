package com.standupsync.repository;

import com.standupsync.model.TeamMember;
import com.standupsync.model.TeamMemberId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TeamMemberRepository extends JpaRepository<TeamMember, TeamMemberId> {

    List<TeamMember> findByTeamId(Long teamId);

    List<TeamMember> findByUserId(String userId);

    Optional<TeamMember> findByTeamIdAndUserId(Long teamId, String userId);

    boolean existsByTeamIdAndUserId(Long teamId, String userId);

    void deleteByTeamIdAndUserId(Long teamId, String userId);
}
