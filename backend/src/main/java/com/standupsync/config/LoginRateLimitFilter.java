package com.standupsync.config;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 登录速率限制：同一IP 1分钟内最多5次尝试
 */
@Component
@Order(1)
public class LoginRateLimitFilter implements Filter {

    private static final Logger log = LoggerFactory.getLogger(LoginRateLimitFilter.class);
    private static final int MAX_ATTEMPTS = 5;
    private static final long WINDOW_MS = 60_000;

    private final Map<String, AttemptWindow> attempts = new ConcurrentHashMap<>();

    private static class AttemptWindow {
        long windowStart;
        int count;
    }

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest request = (HttpServletRequest) req;
        HttpServletResponse response = (HttpServletResponse) res;

        if (request.getRequestURI().equals("/api/auth/login") && "POST".equalsIgnoreCase(request.getMethod())) {
            String ip = request.getRemoteAddr();
            long now = System.currentTimeMillis();

            AttemptWindow window = attempts.computeIfAbsent(ip, k -> new AttemptWindow());

            synchronized (window) {
                if (now - window.windowStart > WINDOW_MS) {
                    window.windowStart = now;
                    window.count = 0;
                }
                window.count++;

                if (window.count > MAX_ATTEMPTS) {
                    log.warn("登录频率限制触发: IP={}, attempts={}", ip, window.count);
                    response.setContentType("application/json;charset=UTF-8");
                    response.setStatus(429);
                    response.getWriter().write(
                        "{\"code\":429,\"message\":\"登录过于频繁，请1分钟后再试\"}");
                    return;
                }
            }
        }

        chain.doFilter(req, res);
    }
}
