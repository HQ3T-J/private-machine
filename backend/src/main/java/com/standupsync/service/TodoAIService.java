package com.standupsync.service;

import com.standupsync.model.TeamMember;
import com.standupsync.repository.TeamMemberRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * 基于规则的智能待办解析服务，不调用任何 LLM。
 */
@Service
public class TodoAIService {

    private final TeamMemberRepository teamMemberRepository;

    // 动作关键词：标识该句子是否是一条待办
    private static final Set<String> ACTION_KEYWORDS = new HashSet<>(Arrays.asList(
            "负责", "完成", "实现", "开发", "设计", "编写", "修改", "更新", "修复", "优化",
            "提交", "部署", "测试", "审核", "确认", "跟进", "处理", "解决", "调研", "准备",
            "创建", "搭建", "配置", "整理", "梳理", "沟通", "协调", "推动", "执行", "输出"
    ));

    // @username 模式
    private static final Pattern AT_PATTERN = Pattern.compile("@(\\S+)");

    // 优先级标志
    // [高] / (HIGH) / !!!  -> HIGH
    // [中] / (MEDIUM) / !! -> MEDIUM
    // [低] / (LOW)  / !    -> LOW
    private static final Pattern PRIORITY_HIGH_PATTERN   = Pattern.compile("\\[高\\]|\\(HIGH\\)|!!!");
    private static final Pattern PRIORITY_MEDIUM_PATTERN = Pattern.compile("\\[中\\]|\\(MEDIUM\\)|!!(?!\\!)");
    private static final Pattern PRIORITY_LOW_PATTERN    = Pattern.compile("\\[低\\]|\\(LOW\\)|(?<!!)!(?!!)");

    public TodoAIService(TeamMemberRepository teamMemberRepository) {
        this.teamMemberRepository = teamMemberRepository;
    }

    // ═══════════════════════════════════════════════
    //  结果 DTO
    // ═══════════════════════════════════════════════

    public static class ParsedTodo {
        private String content;
        private String priority;
        private String suggestedAssignee;

        public ParsedTodo() {}

        public ParsedTodo(String content, String priority, String suggestedAssignee) {
            this.content = content;
            this.priority = priority;
            this.suggestedAssignee = suggestedAssignee;
        }

        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }

        public String getPriority() { return priority; }
        public void setPriority(String priority) { this.priority = priority; }

        public String getSuggestedAssignee() { return suggestedAssignee; }
        public void setSuggestedAssignee(String suggestedAssignee) { this.suggestedAssignee = suggestedAssignee; }
    }

    // ═══════════════════════════════════════════════
    //  核心方法
    // ═══════════════════════════════════════════════

    /**
     * 从自然语言内容中解析出待办事项列表。
     *
     * @param content 自然语言描述的待办文本
     * @param teamId  团队 ID
     * @return 解析出的待办事项列表
     */
    public List<ParsedTodo> generateTodos(String content, Long teamId) {
        if (content == null || content.isBlank()) {
            return new ArrayList<>();
        }

        // 1. 获取团队成员
        List<TeamMember> teamMembers = teamMemberRepository.findByTeamId(teamId);

        // 构建 username -> userId 和 displayName -> userId 的映射
        Map<String, String> usernameToId = teamMembers.stream()
                .collect(Collectors.toMap(
                        m -> m.getUserId(),
                        m -> m.getUserId(),
                        (a, b) -> a));

        // 2. 按换行和句号分隔
        List<String> sentences = splitIntoSentences(content);

        // 3. 解析每条句子
        List<ParsedTodo> todos = new ArrayList<>();
        for (String sentence : sentences) {
            sentence = sentence.trim();
            if (sentence.isEmpty()) {
                continue;
            }

            // 3a. 检查是否包含动作关键词
            boolean hasKeyword = ACTION_KEYWORDS.stream().anyMatch(sentence::contains);
            if (!hasKeyword) {
                continue;
            }

            // 3b. 检测优先级
            String priority = detectPriority(sentence);

            // 3c. 检测责任人
            String suggestedAssignee = detectAssignee(sentence, teamMembers);

            // 3d. 清理内容：移除优先级标记和 @mention
            String cleanContent = cleanSentence(sentence);

            todos.add(new ParsedTodo(cleanContent, priority, suggestedAssignee));
        }

        return todos;
    }

    // ═══════════════════════════════════════════════
    //  辅助方法
    // ═══════════════════════════════════════════════

    /**
     * 按换行符和中文句号分隔句子。
     */
    private List<String> splitIntoSentences(String content) {
        // 先按换行分隔
        List<String> lines = Arrays.asList(content.split("\\r?\\n"));
        List<String> sentences = new ArrayList<>();
        for (String line : lines) {
            line = line.trim();
            if (line.isEmpty()) continue;
            // 按句号进一步分隔（保留非空结果）
            String[] parts = line.split("[。.]");
            for (String part : parts) {
                part = part.trim();
                if (!part.isEmpty()) {
                    sentences.add(part);
                }
            }
        }
        return sentences;
    }

    /**
     * 从句子中检测优先级。
     * 优先级（从高到低）：[高]/(HIGH)/!!! → [中]/(MEDIUM)/!! → [低]/(LOW)/! → 默认 MEDIUM
     */
    private String detectPriority(String sentence) {
        if (PRIORITY_HIGH_PATTERN.matcher(sentence).find()) {
            return "HIGH";
        }
        if (PRIORITY_MEDIUM_PATTERN.matcher(sentence).find()) {
            return "MEDIUM";
        }
        if (PRIORITY_LOW_PATTERN.matcher(sentence).find()) {
            return "LOW";
        }
        return "MEDIUM";
    }

    /**
     * 从句子中检测建议责任人：@username 或直接提及成员 ID / displayName。
     */
    private String detectAssignee(String sentence, List<TeamMember> teamMembers) {
        // 先尝试 @username 模式
        Matcher atMatcher = AT_PATTERN.matcher(sentence);
        if (atMatcher.find()) {
            String mention = atMatcher.group(1);
            // 在团队成员中查找匹配的 userId
            for (TeamMember m : teamMembers) {
                if (m.getUserId().equalsIgnoreCase(mention)
                        || m.getUserId().toLowerCase().contains(mention.toLowerCase())) {
                    return m.getUserId();
                }
            }
        }

        // 再尝试直接在文本中匹配成员 userId
        for (TeamMember m : teamMembers) {
            if (sentence.contains(m.getUserId())) {
                return m.getUserId();
            }
        }

        return null;
    }

    /**
     * 清理句子：移除优先级标记和 @mention。
     */
    private String cleanSentence(String sentence) {
        String result = sentence
                .replaceAll("\\[高\\]|\\[中\\]|\\[低\\]", "")
                .replaceAll("\\(HIGH\\)|\\(MEDIUM\\)|\\(LOW\\)", "")
                .replaceAll("!!!", "")
                .replaceAll("(?<!!)!!(?!\\!)", "")
                .replaceAll("(?<!!)!(?!!)", "")
                .replaceAll("@\\S+", "")
                .replaceAll("\\s+", " ")
                .trim();
        return result;
    }
}
