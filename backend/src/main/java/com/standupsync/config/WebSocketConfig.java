package com.standupsync.config;

import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.MeetingSpeechRepository;
import com.standupsync.websocket.MeetingWebSocketHandler;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final MeetingRepository meetingRepository;
    private final MeetingSpeechRepository meetingSpeechRepository;
    private final ObjectMapper objectMapper;

    public WebSocketConfig(MeetingRepository meetingRepository,
                           MeetingSpeechRepository meetingSpeechRepository,
                           ObjectMapper objectMapper) {
        this.meetingRepository = meetingRepository;
        this.meetingSpeechRepository = meetingSpeechRepository;
        this.objectMapper = objectMapper;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(meetingWebSocketHandler(), "/ws/meetings/{id}")
                .setAllowedOrigins("*");
    }

    @Bean
    public MeetingWebSocketHandler meetingWebSocketHandler() {
        return new MeetingWebSocketHandler(meetingRepository, meetingSpeechRepository, objectMapper);
    }
}
