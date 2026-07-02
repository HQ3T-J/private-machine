package com.standup.todo.config;

import com.standup.todo.entity.TeamMember;
import com.standup.todo.entity.Todo;
import com.standup.todo.repository.TeamMemberRepository;
import com.standup.todo.repository.TodoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final TeamMemberRepository teamMemberRepository;
    private final TodoRepository todoRepository;

    @Override
    public void run(String... args) {
        // 修复 transferRecordHidden 字段默认值问题
        List<Todo> allTodos = todoRepository.findAll();
        for (Todo todo : allTodos) {
            if (todo.getTransferRecordHidden() == null || todo.getTransferRecordHidden()) {
                todo.setTransferRecordHidden(false);
                todoRepository.save(todo);
                System.out.println("✅ 修复待办记录: ID=" + todo.getId() + " transferRecordHidden 设为 false");
            }
        }

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
        String[] users = {"user-001", "user-002", "user-003", "user-004"};
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
