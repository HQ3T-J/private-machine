package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.dto.AuthResponse;
import com.standupsync.dto.LoginRequest;
import com.standupsync.dto.RegisterRequest;
import com.standupsync.model.TeamMember;
import com.standupsync.model.User;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.repository.UserRepository;
import com.standupsync.security.JwtUtil;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public AuthController(UserRepository userRepository,
                          TeamMemberRepository teamMemberRepository,
                          PasswordEncoder passwordEncoder,
                          JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtil = jwtUtil;
    }

    @PostMapping("/register")
    public ApiResponse<AuthResponse> register(@RequestBody RegisterRequest request) {
        if (userRepository.findByUsername(request.getUsername()).isPresent()) {
            return ApiResponse.error(400, "用户名已存在");
        }

        User user = new User();
        user.setUsername(request.getUsername());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setDisplayName(request.getDisplayName() != null ? request.getDisplayName() : request.getUsername());
        user = userRepository.save(user);

        String role = resolveRole(user.getId());
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), role);
        AuthResponse resp = new AuthResponse(token, user.getId(), user.getUsername(), role);
        return ApiResponse.success("注册成功", resp);
    }

    @PostMapping("/login")
    public ApiResponse<AuthResponse> login(@RequestBody LoginRequest request) {
        User user = userRepository.findByUsername(request.getUsername())
                .orElse(null);

        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            return ApiResponse.error(401, "用户名或密码错误");
        }

        String role = resolveRole(user.getId());
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), role);
        AuthResponse resp = new AuthResponse(token, user.getId(), user.getUsername(), role);
        return ApiResponse.success("登录成功", resp);
    }

    /**
     * 根据用户在所有团队中的最高角色确定身份。
     * 优先级: TECH_LEAD > SCRUM_MASTER > DEVELOPER > OBSERVER
     * admin 默认 tech_lead（向后兼容）。
     */
    private String resolveRole(String userId) {
        List<TeamMember> memberships = teamMemberRepository.findByUserId(userId);

        if (memberships.isEmpty()) {
            // 无团队归属，admin 默认 tech_lead
            User user = userRepository.findById(userId).orElse(null);
            if (user != null && "admin".equals(user.getUsername())) {
                return "TECH_LEAD";
            }
            return "DEVELOPER";
        }

        // 取最高角色
        for (TeamMember m : memberships) {
            if (m.getRole() == TeamMember.MemberRole.TECH_LEAD) return "TECH_LEAD";
        }
        for (TeamMember m : memberships) {
            if (m.getRole() == TeamMember.MemberRole.SCRUM_MASTER) return "SCRUM_MASTER";
        }
        for (TeamMember m : memberships) {
            if (m.getRole() == TeamMember.MemberRole.DEVELOPER) return "DEVELOPER";
        }
        return "OBSERVER";
    }
}
