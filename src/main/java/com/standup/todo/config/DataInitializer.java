package com.standup.todo.config;

import com.standup.todo.entity.TeamMember;
import com.standup.todo.repository.TeamMemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final TeamMemberRepository teamMemberRepository;

    @Override
    public void run(String... args) {
        // 创建管理员
        if (!teamMemberRepository.existsByUserIdAndTeamId("admin-001", "team-001")) {
            TeamMember admin = new TeamMember();
            admin.setUserId("admin-001");
            admin.setTeamId("team-001");
            admin.setRole(TeamMember.Role.SCRUM_MASTER);
            teamMemberRepository.save(admin);
            System.out.println("✅ 创建管理员: admin-001");
        }

        // 创建普通用户
        String[] users = {"user-001", "user-002", "user-003"};
        for (String userId : users) {
            if (!teamMemberRepository.existsByUserIdAndTeamId(userId, "team-001")) {
                TeamMember user = new TeamMember();
                user.setUserId(userId);
                user.setTeamId("team-001");
                user.setRole(TeamMember.Role.DEVELOPER);
                teamMemberRepository.save(user);
                System.out.println("✅ 创建普通用户: " + userId);
            }
        }
    }
}
