package com.standupsync.controller;

import com.standupsync.dto.LoginDTO;
import com.standupsync.dto.RegisterDTO;
import com.standupsync.dto.Result;
import com.standupsync.service.UserService;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserService userService;

    public AuthController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping("/register")
    public Result<?> register(@RequestBody RegisterDTO dto) {
        return userService.register(dto.getUsername(), dto.getPassword(), dto.getNickname());
    }

    @PostMapping("/login")
    public Result<?> login(@RequestBody LoginDTO dto) {
        return userService.login(dto);
    }

    @GetMapping("/profile")
    public Result<?> profile(Authentication auth) {
        return userService.profile((Long) auth.getPrincipal());
    }

    @PostMapping("/logout")
    public Result<?> logout(Authentication auth, @RequestHeader("Authorization") String header) {
        String token = header.substring(7);
        return userService.logout((Long) auth.getPrincipal(), token);
    }
}
