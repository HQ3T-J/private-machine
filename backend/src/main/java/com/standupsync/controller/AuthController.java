package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.dto.LoginDTO;
import com.standupsync.dto.RegisterRequest;
import com.standupsync.service.AuthService;

import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public ApiResponse<?> register(@Valid @RequestBody RegisterRequest request) {
        return authService.register(request.getUsername(), request.getPassword(), request.getDisplayName());
    }

    @PostMapping("/login")
    public ApiResponse<?> login(@RequestBody LoginDTO dto) {
        return authService.login(dto.getUsername(), dto.getPassword());
    }

    @GetMapping("/profile")
    public ApiResponse<?> profile(@RequestAttribute("userId") String userId) {
        return authService.getProfile(userId);
    }

    @PostMapping("/logout")
    public ApiResponse<?> logout(@RequestAttribute("userId") String userId,
                                  @RequestHeader("Authorization") String header) {
        return authService.logout(header.substring(7));
    }
}
