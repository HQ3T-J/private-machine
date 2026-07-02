package com.standupsync.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.standupsync.util.JwtUtil;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class StandupWebSocketHandler extends TextWebSocketHandler {

    // standupId -> Set<WebSocketSession>
    private static final Map<String, Set<WebSocketSession>> ROOMS = new ConcurrentHashMap<>();
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final JwtUtil jwtUtil;

    public StandupWebSocketHandler(JwtUtil jwtUtil) {
        this.jwtUtil = jwtUtil;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        String standupId = getStandupId(session);
        ROOMS.computeIfAbsent(standupId, k -> ConcurrentHashMap.newKeySet()).add(session);
        System.out.println("WS connected: standup=" + standupId + " total=" + ROOMS.get(standupId).size());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws IOException {
        String standupId = getStandupId(session);
        String payload = message.getPayload();
        // Broadcast to all OTHER sessions in the same room
        Set<WebSocketSession> room = ROOMS.get(standupId);
        if (room != null) {
            for (WebSocketSession s : room) {
                if (s.isOpen() && !s.getId().equals(session.getId())) {
                    synchronized (s) {
                        s.sendMessage(new TextMessage(payload));
                    }
                }
            }
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        String standupId = getStandupId(session);
        Set<WebSocketSession> room = ROOMS.get(standupId);
        if (room != null) {
            room.remove(session);
            if (room.isEmpty()) ROOMS.remove(standupId);
        }
    }

    public void broadcast(String standupId, String message) {
        Set<WebSocketSession> room = ROOMS.get(standupId);
        if (room != null) {
            for (WebSocketSession s : room) {
                if (s.isOpen()) {
                    try {
                        synchronized (s) {
                            s.sendMessage(new TextMessage(message));
                        }
                    } catch (IOException e) {
                        // session may be dead, ignore
                    }
                }
            }
        }
    }

    public int getRoomSize(String standupId) {
        Set<WebSocketSession> room = ROOMS.get(standupId);
        return room != null ? room.size() : 0;
    }

    private String getStandupId(WebSocketSession session) {
        String path = session.getUri().getPath(); // /ws/standup/{standupId}
        return path.substring(path.lastIndexOf('/') + 1);
    }
}
