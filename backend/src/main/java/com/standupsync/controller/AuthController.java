package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.dto.AuthResponse;
import com.standupsync.dto.LoginDTO;
import com.standupsync.dto.LoginRequest;
import com.standupsync.dto.RegisterRequest;
import com.standupsync.model.TeamMember;
import com.standupsync.model.User;
import com.standupsync.repository.TeamMemberRepository;
import com.standupsync.repository.UserRepository;
import com.standupsync.security.JwtUtil;

import jakarta.validation.Valid;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final TeamMemberRepository teamMemberRepository;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder encoder = new BCryptPasswordEncoder();

    public AuthController(UserRepository userRepository,
                          TeamMemberRepository teamMemberRepository,
                          JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.teamMemberRepository = teamMemberRepository;
        this.jwtUtil = jwtUtil;
    }

    @PostMapping("/register")
    public ApiResponse<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        if (userRepository.findByUsername(request.getUsername()).isPresent())
            return ApiResponse.error(400, "账号已存在");

        User user = new User();
        user.setId(UUID.randomUUID().toString());
        user.setUsername(request.getUsername());
        user.setPasswordHash(encoder.encode(request.getPassword()));
        user.setDisplayName(request.getDisplayName() != null ? request.getDisplayName() : request.getUsername());
        user = userRepository.save(user);

        String role = resolveRole(user.getId());
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), role);

        AuthResponse resp = new AuthResponse(token, user.getId(), user.getUsername(), role);
        return ApiResponse.success("注册成功", resp);
    }

    @PostMapping("/login")
    public ApiResponse<AuthResponse> login(@RequestBody LoginDTO dto) {
        User user = userRepository.findByUsername(dto.getUsername()).orElse(null);
        if (user == null) return ApiResponse.error(401, "账号不存在");
        if (!encoder.matches(dto.getPassword(), user.getPasswordHash()))
            return ApiResponse.error(401, "密码错误");

        String role = resolveRole(user.getId());
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), role);

        AuthResponse resp = new AuthResponse(token, user.getId(), user.getUsername(), role);
        return ApiResponse.success("登录成功", resp);
    }

    @GetMapping("/profile")
    public ApiResponse<User> profile(@RequestAttribute("userId") String userId) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) return ApiResponse.error(404, "用户不存在");
        user.setPasswordHash(null);
        return ApiResponse.success(user);
    }

    @PostMapping("/logout")
    public ApiResponse<?> logout(@RequestAttribute("userId") String userId,
                                  @RequestHeader("Authorization") String header) {
        String token = header.substring(7);
        jwtUtil.addToBlacklist(token);
        return ApiResponse.success("已退出");
    }

    /** 解析用户最高角色: TECH_LEAD > SCRUM_MASTER > DEVELOPER > OBSERVER */
    private String resolveRole(String userId) {
        List<TeamMember> memberships = teamMemberRepository.findByUserId(userId);
        if (memberships.isEmpty()) return "DEVELOPER";
        // admin 用户默认 TECH_LEAD
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
