package com.standupsync.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.standupsync.dto.AnalysisResult;
import com.standupsync.model.MeetingSpeech;
import com.standupsync.model.User;
import com.standupsync.model.User.AIConfig;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * AI analysis service for standup meetings.
 *
 * <h3>Three-step analysis pipeline</h3>
 * <ol>
 *   <li><b>Speaker identification</b> — detect who said what from raw chat log</li>
 *   <li><b>Per-person structured summary</b> — summarise each speaker's update</li>
 *   <li><b>Aggregate + ActionItem extraction</b> — produce meeting summary and action items</li>
 * </ol>
 */
@Service
public class AIService {

    private static final Logger log = LoggerFactory.getLogger(AIService.class);

    /** OpenAI-compatible chat completions endpoint suffix. */
    private static final String CHAT_PATH = "/v1/chat/completions";

    /** Default API base URLs keyed by provider. */
    private static final Map<String, String> BASE_URL_MAP = Map.of(
        "openai",  "https://api.openai.com",
        "doubao",  "https://ark.cn-beijing.volces.com/api/v3",
        "tongyi",  "https://dashscope.aliyuncs.com/compatible-mode/v1"
    );

    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;

    public AIService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.httpClient = new OkHttpClient.Builder()
            .connectTimeout(Duration.ofSeconds(10))
            .readTimeout(Duration.ofSeconds(30))
            .writeTimeout(Duration.ofSeconds(30))
            .callTimeout(Duration.ofSeconds(30))
            .retryOnConnectionFailure(true)
            .build();
    }

    // ─────────────────────────────────────────────────────────────────
    //  Public API
    // ─────────────────────────────────────────────────────────────────

    /**
     * Run the three-step AI analysis pipeline on meeting speeches.
     *
     * @param speeches ordered list of meeting speeches (raw text)
     * @param aiConfig the AI provider + credentials config for the team owner
     * @return structured {@link AnalysisResult} with speaker map, summaries, and action items
     */
    public AnalysisResult analyzeMeeting(List<MeetingSpeech> speeches, AIConfig aiConfig)
            throws IOException {

        if (speeches == null || speeches.isEmpty()) {
            throw new IllegalArgumentException("No speeches provided for analysis");
        }
        if (aiConfig == null) {
            throw new IllegalArgumentException("AI config is required");
        }

        // Build a single chat-log string from all speeches
        StringBuilder chatLogBuilder = new StringBuilder();
        for (int i = 0; i < speeches.size(); i++) {
            MeetingSpeech s = speeches.get(i);
            String label = s.getSpeaker() != null && s.getSpeaker().getDisplayName() != null
                ? s.getSpeaker().getDisplayName()
                : "Speaker" + (i + 1);
            chatLogBuilder.append(label).append(": ").append(s.getRawText()).append("\n\n");
        }
        String chatLog = chatLogBuilder.toString().trim();

        // ── Step 1: Speaker identification ─────────────────────────
        String speakersJson = callLLM(aiConfig, buildSpeakerIdentificationPrompt(chatLog));
        Map<String, String> speakerMap = parseSpeakerMap(speakersJson);

        // ── Step 2: Per-person structured summary ──────────────────
        Map<String, String> personSummaries = new LinkedHashMap<>();
        for (Map.Entry<String, String> entry : speakerMap.entrySet()) {
            String speakerLabel = entry.getKey();
            String speechText = extractSpeakerText(chatLog, speakerLabel);
            if (speechText != null && !speechText.isBlank()) {
                String summary = callLLM(aiConfig, buildPersonSummaryPrompt(speakerLabel, speechText));
                personSummaries.put(speakerLabel, summary);
            }
        }

        // ── Step 3: Aggregate + ActionItem extraction ──────────────
        String aggregateResponse = callLLM(aiConfig, buildAggregatePrompt(chatLog, personSummaries));
        String meetingSummary = extractField(aggregateResponse, "meeting_summary", aggregateResponse);
        String actionItemsJson = extractField(aggregateResponse, "action_items", "[]");

        return new AnalysisResult(speakerMap, personSummaries, meetingSummary, actionItemsJson);
    }

    /**
     * Call an OpenAI-compatible LLM API.
     *
     * @param aiConfig  provider config (provider, model, apiKey, baseUrl)
     * @param systemPrompt  the system-message content
     * @param userPrompt    the user-message content
     * @return the model's text response (content of first choice)
     */
    public String callLLM(AIConfig aiConfig, String systemPrompt, String userPrompt) throws IOException {
        List<Map<String, String>> messages = List.of(
            Map.of("role", "system", "content", systemPrompt),
            Map.of("role", "user",   "content", userPrompt)
        );
        return callLLM(aiConfig, messages);
    }

    /**
     * Call the LLM with an already-constructed messages list.
     */
    public String callLLM(AIConfig aiConfig, List<Map<String, String>> messages) throws IOException {
        String provider = aiConfig.getProvider() != null ? aiConfig.getProvider().toLowerCase() : "openai";
        String model = aiConfig.getModel() != null ? aiConfig.getModel() : "gpt-4o";
        String apiKey = aiConfig.getApiKey();

        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalArgumentException("API key is required for provider: " + provider);
        }

        // Resolve base URL: explicit config → provider map → default openai
        String baseUrl = aiConfig.getBaseUrl();
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = BASE_URL_MAP.getOrDefault(provider, BASE_URL_MAP.get("openai"));
        }
        // Strip trailing slash before appending path
        baseUrl = baseUrl.replaceAll("/+$", "");
        String endpoint = baseUrl + CHAT_PATH;

        // Build request body
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", model);
        body.put("messages", messages);
        body.put("temperature", aiConfig.getTemperature() != null ? aiConfig.getTemperature() : 0.7);
        body.put("max_tokens", aiConfig.getMaxTokens() != null ? aiConfig.getMaxTokens() : 4096);

        String jsonBody;
        try {
            jsonBody = objectMapper.writeValueAsString(body);
        } catch (JsonProcessingException e) {
            throw new IOException("Failed to serialize LLM request body", e);
        }

        Request request = new Request.Builder()
            .url(endpoint)
            .header("Authorization", "Bearer " + apiKey)
            .header("Content-Type", "application/json")
            .post(RequestBody.create(jsonBody, MediaType.parse("application/json")))
            .build();

        // Execute with 1 retry
        IOException lastException = null;
        for (int attempt = 0; attempt < 2; attempt++) {
            try {
                log.debug("LLM call attempt {} to {} with model {}", attempt + 1, endpoint, model);
                try (Response response = httpClient.newCall(request).execute()) {
                    String respBody = response.body() != null ? response.body().string() : "";
                    if (!response.isSuccessful()) {
                        String errorMsg = String.format("LLM API returned %d: %s",
                            response.code(), respBody.length() > 500 ? respBody.substring(0, 500) : respBody);
                        throw new IOException(errorMsg);
                    }
                    return extractContent(respBody);
                }
            } catch (IOException e) {
                lastException = e;
                log.warn("LLM call attempt {} failed: {}", attempt + 1, e.getMessage());
                if (attempt == 0) {
                    // Brief backoff before retry
                    try { Thread.sleep(500); } catch (InterruptedException ignored) { /* continue */ }
                }
            }
        }
        throw new IOException("LLM call failed after 2 attempts", lastException);
    }

    /**
     * Parse a raw meeting chat log into individual speech segments.
     * Splits by newlines and groups by speaker prefix (e.g. "张三: ...").
     *
     * @param rawText the raw chat transcript
     * @return ordered list of parsed speeches with speaker label and text
     */
    public List<Map<String, String>> parseChatLog(String rawText) {
        List<Map<String, String>> speeches = new ArrayList<>();
        if (rawText == null || rawText.isBlank()) {
            return speeches;
        }

        // Pattern: "Name: text" or "Name： text" (full-width colon)
        Pattern linePattern = Pattern.compile("^(.+?)[：:](.+)");
        Map<String, StringBuilder> buffer = new LinkedHashMap<>();
        List<String> order = new ArrayList<>();

        for (String line : rawText.split("\\R")) {
            line = line.trim();
            if (line.isEmpty()) continue;
            Matcher m = linePattern.matcher(line);
            if (m.find()) {
                String speaker = m.group(1).trim();
                String text = m.group(2).trim();
                if (!buffer.containsKey(speaker)) {
                    buffer.put(speaker, new StringBuilder());
                    order.add(speaker);
                }
                buffer.get(speaker).append(text).append("\n");
            } else if (!order.isEmpty()) {
                // Continuation line — append to last speaker
                String lastSpeaker = order.get(order.size() - 1);
                buffer.get(lastSpeaker).append(line).append("\n");
            }
        }

        for (String speaker : order) {
            speeches.add(Map.of("speaker", speaker,
                                "text", buffer.get(speaker).toString().trim()));
        }
        return speeches;
    }

    /**
     * Extract JSON from raw LLM output that may be wrapped in markdown code fences
     * or contain surrounding text.
     *
     * @param raw the raw LLM response text
     * @return the extracted JSON string, or the original raw if no JSON block found
     */
    public String extractJson(String raw) {
        if (raw == null || raw.isBlank()) return raw;

        // Try to find JSON inside ```json fences first
        Pattern fencePattern = Pattern.compile(
            "```(?:json)?\\s*\\n?([\\s\\S]*?)```", Pattern.CASE_INSENSITIVE);
        Matcher fm = fencePattern.matcher(raw);
        if (fm.find()) {
            return fm.group(1).trim();
        }

        // Try to find a JSON object { ... } in the text
        Pattern jsonPattern = Pattern.compile("\\{[^{}]*(?:\\{[^{}]*}[^{}]*)*}", Pattern.DOTALL);
        Matcher jm = jsonPattern.matcher(raw);
        if (jm.find()) {
            return jm.group().trim();
        }

        // Fallback: return the raw text
        return raw.trim();
    }

    // ─────────────────────────────────────────────────────────────────
    //  Internal helpers
    // ─────────────────────────────────────────────────────────────────

    /** Convenience: call LLM with a single user prompt (system prompt built-in). */
    private String callLLM(AIConfig aiConfig, String userPrompt) throws IOException {
        return callLLM(aiConfig,
            "You are a helpful assistant. Respond with valid JSON only, no markdown fences or extra text.",
            userPrompt);
    }

    /** Extract "content" field from OpenAI-style API response. */
    private String extractContent(String respBody) throws IOException {
        try {
            JsonNode root = objectMapper.readTree(respBody);
            JsonNode choices = root.get("choices");
            if (choices == null || !choices.isArray() || choices.isEmpty()) {
                throw new IOException("No choices in LLM response: " + truncate(respBody));
            }
            JsonNode message = choices.get(0).get("message");
            if (message == null) {
                throw new IOException("No message in first choice");
            }
            JsonNode content = message.get("content");
            if (content == null) {
                throw new IOException("No content in message");
            }
            return content.asText().trim();
        } catch (JsonProcessingException e) {
            throw new IOException("Failed to parse LLM response JSON: " + truncate(respBody), e);
        }
    }

    // ── Prompt builders ──────────────────────────────────────────────

    private String buildSpeakerIdentificationPrompt(String chatLog) {
        return """
            Below is a chat log from a team standup meeting. Each line starts with a speaker label (e.g. "Alice: ...").
            Your task is to identify the unique speakers and return a JSON object mapping each label to the person's name.

            Chat log:
            %s

            Respond with ONLY a JSON object like:
            {"label1": "Full Name", "label2": "Full Name"}
            """.formatted(chatLog);
    }

    private String buildPersonSummaryPrompt(String speaker, String speechText) {
        return """
            Summarise the following standup update from %s into a structured format.
            Include these sections if present:
            - What was accomplished since last standup
            - What will be worked on next
            - Any blockers or challenges

            Update:
            %s

            Respond with a concise plain-text summary, no JSON needed.
            """.formatted(speaker, speechText);
    }

    private String buildAggregatePrompt(String chatLog, Map<String, String> personSummaries) {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, String> e : personSummaries.entrySet()) {
            sb.append("## ").append(e.getKey()).append("\n").append(e.getValue()).append("\n\n");
        }

        return """
            You are analysing a team standup meeting. Below is the raw chat log followed by per-person summaries.
            Produce a JSON object with two fields:
            1. "meeting_summary": a 2-3 paragraph overall meeting summary.
            2. "action_items": a JSON array of action items, each with fields: "content", "assignee", "priority" (HIGH/MEDIUM/LOW).

            Raw chat log:
            %s

            Per-person summaries:
            %s

            Respond with ONLY valid JSON:
            {"meeting_summary": "...", "action_items": [{"content": "...", "assignee": "Name", "priority": "HIGH"}, ...]}
            """.formatted(chatLog, sb.toString().trim());
    }

    // ── Response parsers ─────────────────────────────────────────────

    private Map<String, String> parseSpeakerMap(String llmResponse) {
        String json = extractJson(llmResponse);
        Map<String, String> result = new LinkedHashMap<>();
        try {
            JsonNode root = objectMapper.readTree(json);
            root.fields().forEachRemaining(f -> result.put(f.getKey(), f.getValue().asText()));
        } catch (JsonProcessingException e) {
            log.warn("Failed to parse speaker map JSON, using raw response: {}", e.getMessage());
        }
        return result;
    }

    /** Extract a named field from a JSON object string. */
    private String extractField(String json, String field, String fallback) {
        String clean = extractJson(json);
        try {
            JsonNode node = objectMapper.readTree(clean);
            JsonNode fieldNode = node.get(field);
            if (fieldNode != null) {
                return fieldNode.isTextual() ? fieldNode.asText() : fieldNode.toString();
            }
        } catch (JsonProcessingException e) {
            log.warn("Failed to extract field '{}' from JSON", field);
        }
        return fallback;
    }

    /** Extract the text spoken by a particular speaker label from the chat log. */
    private String extractSpeakerText(String chatLog, String speakerLabel) {
        Pattern p = Pattern.compile(
            Pattern.quote(speakerLabel) + "\\s*[：:]\\s*(.+?)(?=(?:\\n\\s*\\n|\\n[A-Za-z\\u4e00-\\u9fff]+[：:]|$))",
            Pattern.DOTALL);
        Matcher m = p.matcher(chatLog);
        if (m.find()) {
            return m.group(1).trim();
        }
        return null;
    }

    private static String truncate(String s) {
        return s.length() > 300 ? s.substring(0, 300) + "..." : s;
    }

    /**
     * 解析自由文本发言为结构化 昨天/今天/阻碍。
     * 优先使用 LLM，不可用时降级为规则引擎。
     */
    public Map<String, String> parseFreeText(String text, com.standupsync.config.AIServerConfig aiConfig) {
        if (aiConfig != null && aiConfig.isEnabled()) {
            try {
                return parseWithLLM(text, aiConfig);
            } catch (Exception e) {
                log.warn("AI 解析失败，降级为规则引擎: {}", e.getMessage());
            }
        }
        return parseWithRules(text);
    }

    private Map<String, String> parseWithLLM(String text, com.standupsync.config.AIServerConfig aiConfig) throws IOException {
        String systemPrompt = """
            你是一个专业的敏捷开发站会秘书。你的任务是将团队成员的发言精确地拆分为三个结构化字段。

            ## 分类规则

            **yesterday (昨天完成了什么)**
            - 已完成的任务、已修复的bug、已上线的功能
            - 已完成的代码审查、已通过的测试
            - 已交付的文档、已完成的会议
            - 提示词: 昨天、完成了、已经、修复了、上线了、交付了、做完了

            **today (今天计划做什么)**
            - 计划开始的任务、正在进行的工作
            - 准备编写的代码、即将开始的开发
            - 安排好的会议、计划中的测试
            - 提示词: 今天、准备、计划、开始、进行、继续、接下来

            **blockers (阻碍/风险)**
            - 阻塞当前工作的外部依赖
            - 等待他人响应、需要他人协助
            - 技术难题、环境问题、资源不足
            - 需求不明确、方案待确认
            - 提示词: 阻碍、卡住了、等待、需要...帮助、依赖、blocked by

            ## 输出要求
            1. 每个字段提取核心内容，去除冗余的语气词和连接词
            2. 保留关键技术细节（模块名、功能名、bug编号等）
            3. 如果某类信息在发言中完全没有提及，该字段留空字符串 ""
            4. 不要添加原文没有的信息
            5. 使用简洁专业的语言，每条控制在80字以内
            6. 多条内容用分号分隔

            ## 示例

            输入: "昨天把登录模块重构完了，修了3个样式bug；今天开始做权限管理，下午有个技术评审；目前卡在接口文档还没对齐"
            输出: {"yesterday": "完成登录模块重构；修复3个样式bug", "today": "开始权限管理开发；参加技术评审", "blockers": "接口文档未对齐"}

            输入: "continuing work on the dashboard API, should finish by EOD. blocked by the design team not providing final mockups yet"
            输出: {"yesterday": "", "today": "继续Dashboard API开发，预计今日完成", "blockers": "设计团队未提供最终mockup"}

            输入: "今天主要排查线上内存泄漏问题，已经定位到是缓存模块"
            输出: {"yesterday": "", "today": "排查并定位缓存模块内存泄漏问题", "blockers": ""}

            输入: "nothing to report"
            输出: {"yesterday": "", "today": "", "blockers": ""}

            返回纯JSON，不要markdown代码块，不要任何其他文字。""";

        String userPrompt = "请分析以下站会发言:\n\n" + text;

        User.AIConfig cfg = new User.AIConfig();
        cfg.setProvider(aiConfig.getProvider());
        cfg.setModel(aiConfig.getModel());
        cfg.setApiKey(aiConfig.getApiKey());
        if (aiConfig.getBaseUrl() != null && !aiConfig.getBaseUrl().isBlank())
            cfg.setBaseUrl(aiConfig.getBaseUrl());
        cfg.setTemperature(aiConfig.getTemperature());
        cfg.setMaxTokens(aiConfig.getMaxTokens());

        String response = callLLM(cfg, systemPrompt, userPrompt);
        String json = extractJson(response);
        return objectMapper.readValue(json, new com.fasterxml.jackson.core.type.TypeReference<Map<String, String>>() {});
    }

    private Map<String, String> parseWithRules(String text) {
        Map<String, String> result = new LinkedHashMap<>();
        result.put("yesterday", "");
        result.put("today", "");
        result.put("blockers", "");

        String lower = text.toLowerCase();
        String[] yesterdayKeys = {"昨天", "昨日", "完成了", "做了", "yesterday", "done", "finished", "accomplished"};
        String[] todayKeys = {"今天", "今日", "计划", "要做", "准备", "today", "plan", "will", "going to"};
        String[] blockerKeys = {"阻碍", "困难", "问题", "卡住", "需要帮助", "等待", "blocker", "blocked", "stuck", "need help", "waiting"};

        List<int[]> segments = new ArrayList<>();
        for (String kw : yesterdayKeys) { int i = lower.indexOf(kw); if (i >= 0) segments.add(new int[]{i, i + kw.length(), 0}); }
        for (String kw : todayKeys) { int i = lower.indexOf(kw); if (i >= 0) segments.add(new int[]{i, i + kw.length(), 1}); }
        for (String kw : blockerKeys) { int i = lower.indexOf(kw); if (i >= 0) segments.add(new int[]{i, i + kw.length(), 2}); }

        if (segments.isEmpty()) {
            result.put("today", text.trim());
            return result;
        }

        segments.sort(java.util.Comparator.comparingInt(a -> a[0]));
        for (int i = 0; i < segments.size(); i++) {
            int[] seg = segments.get(i);
            int start = seg[1];
            int end = (i + 1 < segments.size()) ? segments.get(i + 1)[0] : text.length();
            String content = text.substring(start, end).trim().replaceAll("^[：:，,。；;\\s]+", "").trim();
            switch (seg[2]) {
                case 0 -> result.put("yesterday", content);
                case 1 -> result.put("today", content);
                case 2 -> result.put("blockers", content);
            }
        }

        if (result.get("today").isBlank() && result.get("yesterday").isBlank())
            result.put("today", text.trim());

        return result;
    }
}
