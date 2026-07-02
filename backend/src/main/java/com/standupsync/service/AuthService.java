package com.standupsync.service;

import com.standupsync.dto.ApiResponse;
import com.standupsync.dto.AuthResponse;
import com.standupsync.model.TeamMember;
import com.standupsync.model.User;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.repository.UserRepository;
import com.standupsync.security.JwtUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final UserRepository userRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder encoder;

    public AuthService(UserRepository userRepository,
                       TeamMemberRepository teamMemberRepository,
                       JwtUtil jwtUtil,
                       PasswordEncoder encoder) {
        this.userRepository = userRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.jwtUtil = jwtUtil;
        this.encoder = encoder;
    }

    public ApiResponse<AuthResponse> register(String username, String password, String displayName) {
        if (username == null || username.trim().isEmpty()) return ApiResponse.error(400, "用户名不能为空");
        if (password == null || password.trim().isEmpty()) return ApiResponse.error(400, "密码不能为空");
        if (userRepository.findByUsername(username.trim()).isPresent())
            return ApiResponse.error(400, "账号已存在");

        User user = new User();
        user.setId(UUID.randomUUID().toString());
        user.setUsername(username.trim());
        user.setPasswordHash(encoder.encode(password));
        user.setDisplayName(displayName != null ? displayName.trim() : username.trim());
        user = userRepository.save(user);

        String role = resolveRole(user.getId());
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), role);
        AuthResponse resp = new AuthResponse(token, user.getId(), user.getUsername(), role);
        return ApiResponse.success("注册成功", resp);
    }

    public ApiResponse<AuthResponse> login(String username, String password) {
        if (username == null || password == null)
            return ApiResponse.error(401, "用户名和密码不能为空");

        User user = userRepository.findByUsername(username.trim()).orElse(null);
        if (user == null) return ApiResponse.error(401, "账号不存在");
        if (!encoder.matches(password, user.getPasswordHash()))
            return ApiResponse.error(401, "密码错误");

        String role = resolveRole(user.getId());
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), role);
        AuthResponse resp = new AuthResponse(token, user.getId(), user.getUsername(), role);
        return ApiResponse.success("登录成功", resp);
    }

    public ApiResponse<User> getProfile(String userId) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) return ApiResponse.error(404, "用户不存在");
        user.setPasswordHash(null);
        return ApiResponse.success(user);
    }

    public ApiResponse<?> logout(String token) {
        jwtUtil.addToBlacklist(token);
        return ApiResponse.success("已退出");
    }

    private String resolveRole(String userId) {
        List<TeamMember> memberships = teamMemberRepository.findByUserId(userId);
        if (memberships.isEmpty()) return "DEVELOPER";
        User user = userRepository.findById(userId).orElse(null);
        if (user != null && "admin".equals(user.getUsername())) return "TECH_LEAD";
        for (TeamMember m : memberships)
            if (m.getRole() == TeamMember.MemberRole.TECH_LEAD) return "TECH_LEAD";
        for (TeamMember m : memberships)
            if (m.getRole() == TeamMember.MemberRole.SCRUM_MASTER) return "SCRUM_MASTER";
        for (TeamMember m : memberships)
            if (m.getRole() == TeamMember.MemberRole.DEVELOPER) return "DEVELOPER";
        return "OBSERVER";
    }
}
