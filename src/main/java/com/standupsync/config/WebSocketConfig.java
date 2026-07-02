package com.standupsync.config;

import com.standupsync.websocket.StandupWebSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final StandupWebSocketHandler handler;

    public WebSocketConfig(StandupWebSocketHandler handler) {
        this.handler = handler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(handler, "/ws/standup/{standupId}")
                .setAllowedOrigins("*");
        registry.addHandler(handler, "/ws/team/{teamId}")
                .setAllowedOrigins("*");
    }
}
