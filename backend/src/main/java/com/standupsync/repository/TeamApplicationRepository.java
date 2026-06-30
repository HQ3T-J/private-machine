package com.standupsync.repository;

import com.standupsync.model.TeamApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TeamApplicationRepository extends JpaRepository<TeamApplication, Long> {

    List<TeamApplication> findByTeamIdAndStatus(Long teamId, Integer status);

    List<TeamApplication> findByTeamId(Long teamId);

    boolean existsByTeamIdAndUserIdAndStatus(Long teamId, String userId, Integer status);
}
