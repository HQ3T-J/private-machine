package com.standupsync.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.standupsync.entity.StandupRecord;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@Service
public class AIService {

    @Value("${ai.api-url}")
    private String apiUrl;

    @Value("${ai.api-token}")
    private String apiToken;

    @Value("${ai.model}")
    private String model;

    @Value("${ai.timeout}")
    private int timeout;

    private final ObjectMapper mapper = new ObjectMapper();

    /**
     * Generate structured summary from standup speeches.
     * Tries real AI API first, falls back to local heuristic extraction.
     */
    public Map<String, Object> summarize(Long standupId, List<StandupRecord> records) {
        // 1. Try real AI API
        Map<String, Object> aiResult = callAiApi(records);
        if (aiResult != null) return aiResult;

        // 2. Fallback: local heuristic extraction (always works)
        return localSummarize(records);
    }

    private Map<String, Object> callAiApi(List<StandupRecord> records) {
        try {
            // Build speech summary text
            StringBuilder sb = new StringBuilder();
            for (StandupRecord r : records) {
                if (!"done".equals(r.getSpeakStatus())) continue;
                sb.append("发言人").append(r.getUserId()).append(":\n");
                sb.append("- 昨日完成: ").append(r.getYesterdayWork() != null ? r.getYesterdayWork() : "无").append("\n");
                sb.append("- 今日计划: ").append(r.getTodayPlan() != null ? r.getTodayPlan() : "无").append("\n");
                sb.append("- 阻碍: ").append(r.getBlockers() != null && !r.getBlockers().isEmpty() ? r.getBlockers() : "无").append("\n\n");
            }

            if (sb.length() == 0) {
                // No speeches to summarize
                return buildEmptyResult();
            }

            // Build system prompt
            String systemPrompt = "你是一个敏捷站会助手。根据发言记录生成结构化纪要。只返回JSON，不要任何解释。";

            // Build user prompt
            String userPrompt = "根据以下站会发言记录，生成结构化纪要：\n\n" + sb.toString() + "\n"
                    + "返回JSON格式（只返回JSON，不要markdown代码块）：\n"
                    + "{\n"
                    + "  \"doneList\": [\"发言人N: 完成的具体工作\"],\n"
                    + "  \"planList\": [\"发言人N: 今日计划\"],\n"
                    + "  \"blockers\": [{\"text\": \"阻碍描述\", \"type\": \"技术问题/资源问题/沟通问题\", \"reporter\": \"发言人ID\"}],\n"
                    + "  \"actionItems\": [{\"content\": \"行动项内容\", \"assigneeId\": \"发言人ID\", \"priority\": \"high/medium/low\"}]\n"
                    + "}";

            // Build request body
            Map<String, Object> requestMap = new HashMap<>();
            requestMap.put("model", model);
            requestMap.put("max_tokens", 2000);

            List<Map<String, String>> messages = new ArrayList<>();
            Map<String, String> sysMsg = new HashMap<>();
            sysMsg.put("role", "system");
            sysMsg.put("content", systemPrompt);
            messages.add(sysMsg);

            Map<String, String> userMsg = new HashMap<>();
            userMsg.put("role", "user");
            userMsg.put("content", userPrompt);
            messages.add(userMsg);

            requestMap.put("messages", messages);

            String requestBody = mapper.writeValueAsString(requestMap);

            // Call AI API
            RestTemplate restTemplate = new RestTemplate();
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiToken);
            HttpEntity<String> entity = new HttpEntity<>(requestBody, headers);

            System.out.println("Calling AI API...");
            ResponseEntity<String> response = restTemplate.exchange(apiUrl, HttpMethod.POST, entity, String.class);

            if (response.getStatusCodeValue() == 200) {
                String body = response.getBody();
                System.out.println("AI response received, length: " + (body != null ? body.length() : 0));

                // Try to parse JSON from AI response
                String json = extractJson(body);
                if (json != null) {
                    JsonNode root = mapper.readTree(json);
                    Map<String, Object> result = new HashMap<>();
                    result.put("doneList", jsonArrayToList(root.get("doneList")));
                    result.put("planList", jsonArrayToList(root.get("planList")));

                    List<Map<String, Object>> blockerList = new ArrayList<>();
                    JsonNode blockersNode = root.get("blockers");
                    if (blockersNode != null && blockersNode.isArray()) {
                        for (JsonNode b : blockersNode) {
                            Map<String, Object> blocker = new HashMap<>();
                            blocker.put("text", b.has("text") ? b.get("text").asText() : "");
                            blocker.put("type", b.has("type") ? b.get("type").asText() : "技术问题");
                            blocker.put("reporter", b.has("reporter") ? b.get("reporter").asText() : "");
                            blockerList.add(blocker);
                        }
                    }
                    result.put("blockers", blockerList);

                    List<Map<String, Object>> actionList = new ArrayList<>();
                    JsonNode actionsNode = root.get("actionItems");
                    if (actionsNode != null && actionsNode.isArray()) {
                        for (JsonNode a : actionsNode) {
                            Map<String, Object> action = new HashMap<>();
                            action.put("content", a.has("content") ? a.get("content").asText() : "");
                            action.put("assigneeId", a.has("assigneeId") ? a.get("assigneeId").asText() : "1");
                            action.put("priority", a.has("priority") ? a.get("priority").asText() : "medium");
                            actionList.add(action);
                        }
                    }
                    result.put("actionItems", actionList);

                    return result;
                }

                // Couldn't parse JSON — return raw text as fallback
                Map<String, Object> fallback = buildEmptyResult();
                fallback.put("fallbackText", body);
                return fallback;
            }
        } catch (Exception e) {
            System.err.println("AI call failed: " + e.getMessage());
            e.printStackTrace();
        }
        return null; // Signal caller to use pure fallback
    }

    private String extractJson(String text) {
        if (text == null) return null;
        // Try to find JSON block
        int start = text.indexOf("{");
        int end = text.lastIndexOf("}");
        if (start >= 0 && end > start) {
            return text.substring(start, end + 1);
        }
        return null;
    }

    private List<String> jsonArrayToList(JsonNode node) {
        List<String> list = new ArrayList<>();
        if (node != null && node.isArray()) {
            for (JsonNode item : node) {
                list.add(item.asText());
            }
        }
        return list;
    }

    private Map<String, Object> buildEmptyResult() {
        Map<String, Object> result = new HashMap<>();
        result.put("doneList", Collections.emptyList());
        result.put("planList", Collections.emptyList());
        result.put("blockers", Collections.emptyList());
        result.put("actionItems", Collections.emptyList());
        return result;
    }

    /**
     * Local heuristic summarization when AI API is unavailable.
     * Extracts structured data from the 3-column inputs without AI.
     */
    private Map<String, Object> localSummarize(List<StandupRecord> records) {
        List<String> doneList = new ArrayList<>();
        List<String> planList = new ArrayList<>();
        List<Map<String, Object>> blockerList = new ArrayList<>();
        List<Map<String, Object>> actionList = new ArrayList<>();

        for (StandupRecord r : records) {
            if (!"done".equals(r.getSpeakStatus())) continue;
            String uid = String.valueOf(r.getUserId());

            // Extract yesterday work
            if (r.getYesterdayWork() != null && !r.getYesterdayWork().trim().isEmpty()) {
                String[] lines = r.getYesterdayWork().split("[\\n。；;]");
                for (String line : lines) {
                    line = line.trim();
                    if (!line.isEmpty()) {
                        doneList.add("用户" + uid + "：" + line);
                    }
                }
            }

            // Extract today plan
            if (r.getTodayPlan() != null && !r.getTodayPlan().trim().isEmpty()) {
                String[] lines = r.getTodayPlan().split("[\\n。；;]");
                for (String line : lines) {
                    line = line.trim();
                    if (!line.isEmpty()) {
                        planList.add("用户" + uid + "：" + line);
                    }
                }
            }

            // Extract blockers
            if (r.getBlockers() != null && !r.getBlockers().trim().isEmpty()) {
                String blockerText = r.getBlockers().trim();
                Map<String, Object> blocker = new HashMap<>();
                blocker.put("text", "用户" + uid + "：" + blockerText);
                // Simple heuristic: classify blocker type
                if (blockerText.contains("测试") || blockerText.contains("环境") || blockerText.contains("bug") || blockerText.contains("数据库") || blockerText.contains("API") || blockerText.contains("文档")) {
                    blocker.put("type", "技术问题");
                } else if (blockerText.contains("等") || blockerText.contains("沟通") || blockerText.contains("设计") || blockerText.contains("确认")) {
                    blocker.put("type", "沟通问题");
                } else {
                    blocker.put("type", "资源问题");
                }
                blocker.put("reporter", uid);
                blockerList.add(blocker);

                // Generate an action item for each blocker
                Map<String, Object> action = new HashMap<>();
                action.put("content", "处理：" + blockerText);
                action.put("assigneeId", uid);
                // Priority heuristic
                if (blockerText.contains("紧急") || blockerText.contains("重要") || blockerText.contains("bug") || blockerText.contains("数据库")) {
                    action.put("priority", "high");
                } else if (blockerText.contains("文档") || blockerText.contains("优化")) {
                    action.put("priority", "low");
                } else {
                    action.put("priority", "medium");
                }
                actionList.add(action);
            }
        }

        // If no blockers found, add a default action
        if (actionList.isEmpty() && !doneList.isEmpty()) {
            Map<String, Object> defaultAction = new HashMap<>();
            defaultAction.put("content", "Code Review 本次改动");
            defaultAction.put("assigneeId", "1");
            defaultAction.put("priority", "medium");
            actionList.add(defaultAction);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("doneList", doneList);
        result.put("planList", planList);
        result.put("blockers", blockerList);
        result.put("actionItems", actionList);
        return result;
    }
}
