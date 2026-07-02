package com.standupsync.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.standupsync.dto.LoginDTO;
import com.standupsync.dto.Result;
import com.standupsync.entity.User;
import com.standupsync.mapper.UserMapper;
import com.standupsync.util.JwtUtil;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import java.util.HashMap;
import java.util.Map;

@Service
public class UserService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public UserService(UserMapper userMapper, PasswordEncoder passwordEncoder, JwtUtil jwtUtil) {
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtil = jwtUtil;
    }

    public Result<?> register(String username, String password, String nickname) {
        User exist = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (exist != null) return Result.fail("账号已存在");
        User user = new User();
        user.setUsername(username);
        user.setPassword(passwordEncoder.encode(password));
        user.setNickname(nickname != null ? nickname : username);
        userMapper.insert(user);
        return Result.ok("注册成功");
    }

    public Result<?> login(LoginDTO dto) {
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getUsername, dto.getUsername()));
        if (user == null) return Result.fail("账号不存在");
        if (!passwordEncoder.matches(dto.getPassword(), user.getPassword())) return Result.fail("密码错误");
        String token = jwtUtil.generateToken(user.getId(), user.getUsername());
        user.setJwtToken(token);
        userMapper.updateById(user);
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("userId", user.getId());
        data.put("nickname", user.getNickname());
        return Result.ok("登录成功", data);
    }

    public Result<?> profile(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) return Result.fail("用户不存在");
        user.setPassword(null);
        user.setJwtToken(null);
        return Result.ok(user);
    }

    public Result<?> logout(Long userId, String token) {
        jwtUtil.addToBlacklist(token);
        return Result.ok("已退出");
    }
}
