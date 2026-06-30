package com.standupsync.websocket;

import com.standupsync.model.Meeting;
import com.standupsync.model.MeetingSpeech;
import com.standupsync.model.User;
import com.standupsync.repository.MeetingRepository;
import com.standupsync.repository.MeetingSpeechRepository;
import com.standupsync.security.JwtUtil;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.net.URI;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 处理 /ws/meetings/{id} 的 WebSocket 连接。
 * 消息类型: submit_speech, speech_update, timer_sync, meeting_ended
 */
public class MeetingWebSocketHandler extends TextWebSocketHandler {

    private static final Logger log = LoggerFactory.getLogger(MeetingWebSocketHandler.class);

    // meetingId -> Set<WebSocketSession>
    private static final ConcurrentHashMap<Long, Set<WebSocketSession>> rooms = new ConcurrentHashMap<>();
    // session -> userId
    private static final ConcurrentHashMap<String, String> sessionUsers = new ConcurrentHashMap<>();

    private final MeetingRepository meetingRepository;
    private final MeetingSpeechRepository meetingSpeechRepository;
    private final ObjectMapper objectMapper;

    public MeetingWebSocketHandler(MeetingRepository meetingRepository,
                                   MeetingSpeechRepository meetingSpeechRepository,
                                   ObjectMapper objectMapper) {
        this.meetingRepository = meetingRepository;
        this.meetingSpeechRepository = meetingSpeechRepository;
        this.objectMapper = objectMapper;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        Long meetingId = extractMeetingId(session);
        String userId = authenticate(session);

        if (meetingId == null || userId == null) {
            session.close(CloseStatus.BAD_DATA);
            return;
        }

        // 验证会议存在
        Meeting meeting = meetingRepository.findById(meetingId).orElse(null);
        if (meeting == null) {
            session.close(CloseStatus.BAD_DATA);
            return;
        }

        sessionUsers.put(session.getId(), userId);
        rooms.computeIfAbsent(meetingId, k -> ConcurrentHashMap.newKeySet()).add(session);

        log.info("WebSocket 连接: userId={}, meetingId={}", userId, meetingId);
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String userId = sessionUsers.get(session.getId());
        Long meetingId = extractMeetingId(session);
        if (userId == null || meetingId == null) return;

        JsonNode json = objectMapper.readTree(message.getPayload());
        String type = json.has("type") ? json.get("type").asText() : "";

        switch (type) {
            case "submit_speech" -> handleSubmitSpeech(session, meetingId, userId, json);
            case "speech_update" -> handleSpeechUpdate(session, meetingId, userId, json);
            case "timer_sync" -> handleTimerSync(session, meetingId, userId, json);
            case "meeting_ended" -> handleMeetingEnded(session, meetingId, userId, json);
            default -> log.warn("未知消息类型: {}", type);
        }
    }

    private void handleSubmitSpeech(WebSocketSession session, Long meetingId, String userId, JsonNode json)
            throws IOException {
        String content = json.has("content") ? json.get("content").asText() : "";

        MeetingSpeech speech = new MeetingSpeech();
        Meeting meeting = new Meeting();
        meeting.setId(meetingId);
        speech.setMeeting(meeting);
        User speaker = new User();
        speaker.setId(userId);
        speech.setSpeaker(speaker);
        speech.setRawText(content);
        speech.setInputMethod(MeetingSpeech.InputMethod.TEXT);
        speech = meetingSpeechRepository.save(speech);

        // 广播发言提交事件
        Map<String, Object> broadcast = new HashMap<>();
        broadcast.put("type", "speech_submitted");
        broadcast.put("speechId", speech.getId());
        broadcast.put("userId", userId);
        broadcast.put("content", content);
        broadcast.put("createdAt", speech.getCreatedAt() != null ? speech.getCreatedAt().toString() : "");

        broadcastToRoom(meetingId, objectMapper.writeValueAsString(broadcast));
    }

    private void handleSpeechUpdate(WebSocketSession session, Long meetingId, String userId, JsonNode json)
            throws IOException {
        Map<String, Object> broadcast = new HashMap<>();
        broadcast.put("type", "speech_update");
        broadcast.put("userId", userId);
        if (json.has("currentSpeakerId")) {
            broadcast.put("currentSpeakerId", json.get("currentSpeakerId").asText());
        }
        if (json.has("status")) {
            broadcast.put("status", json.get("status").asText());
        }

        broadcastToRoom(meetingId, objectMapper.writeValueAsString(broadcast));
    }

    private void handleTimerSync(WebSocketSession session, Long meetingId, String userId, JsonNode json)
            throws IOException {
        Map<String, Object> broadcast = new HashMap<>();
        broadcast.put("type", "timer_sync");
        broadcast.put("userId", userId);
        if (json.has("remaining")) {
            broadcast.put("remaining", json.get("remaining").asLong());
        }
        if (json.has("action")) {
            broadcast.put("action", json.get("action").asText());
        }

        broadcastToRoom(meetingId, objectMapper.writeValueAsString(broadcast));
    }

    private void handleMeetingEnded(WebSocketSession session, Long meetingId, String userId, JsonNode json)
            throws IOException {
        Map<String, Object> broadcast = new HashMap<>();
        broadcast.put("type", "meeting_ended");
        broadcast.put("userId", userId);
        broadcast.put("meetingId", meetingId);

        broadcastToRoom(meetingId, objectMapper.writeValueAsString(broadcast));
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        Long meetingId = extractMeetingId(session);
        String userId = sessionUsers.remove(session.getId());

        if (meetingId != null) {
            Set<WebSocketSession> sessions = rooms.get(meetingId);
            if (sessions != null) {
                sessions.remove(session);
                if (sessions.isEmpty()) {
                    rooms.remove(meetingId);
                }
            }
        }
        log.info("WebSocket 断开: userId={}, meetingId={}", userId, meetingId);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        log.error("WebSocket 传输错误: sessionId={}", session.getId(), exception);
    }

    private Long extractMeetingId(WebSocketSession session) {
        URI uri = session.getUri();
        if (uri == null) return null;
        String path = uri.getPath();
        String[] parts = path.split("/");
        if (parts.length >= 4) {
            try {
                return Long.parseLong(parts[3]);
            } catch (NumberFormatException e) {
                return null;
            }
        }
        return null;
    }

    private String authenticate(WebSocketSession session) {
        URI uri = session.getUri();
        if (uri == null) return null;
        String query = uri.getQuery();
        if (query == null) return null;

        JwtUtil jwtUtil = new JwtUtil("standupsync-jwt-secret-key-2026", 86400000);
        for (String param : query.split("&")) {
            String[] kv = param.split("=", 2);
            if (kv.length == 2 && "token".equals(kv[0])) {
                try {
                    if (jwtUtil.validateToken(kv[1])) {
                        return jwtUtil.getUserId(kv[1]);
                    }
                } catch (Exception e) {
                    log.warn("JWT 解析失败: {}", e.getMessage());
                    return null;
                }
            }
        }
        return null;
    }

    private void broadcastToRoom(Long meetingId, String message) {
        Set<WebSocketSession> sessions = rooms.get(meetingId);
        if (sessions == null || sessions.isEmpty()) return;

        TextMessage textMessage = new TextMessage(message);
        for (WebSocketSession ws : sessions) {
            if (ws.isOpen()) {
                try {
                    ws.sendMessage(textMessage);
                } catch (IOException e) {
                    log.error("广播消息失败: sessionId={}", ws.getId(), e);
                }
            }
        }
    }
}
