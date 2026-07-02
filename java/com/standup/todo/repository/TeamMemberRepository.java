package com.standup.todo.repository;

import com.standup.todo.entity.TeamMember;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TeamMemberRepository extends JpaRepository<TeamMember, Long> {

    Optional<TeamMember> findByUserIdAndTeamId(String userId, String teamId);

    List<TeamMember> findByTeamId(String teamId);

    boolean existsByUserIdAndTeamId(String userId, String teamId);

    boolean existsByUserIdAndTeamIdAndRole(String userId, String teamId, TeamMember.Role role);
}
