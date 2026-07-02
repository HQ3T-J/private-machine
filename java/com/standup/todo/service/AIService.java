package com.standup.todo.service;

import com.standup.todo.dto.AIGenerateResponse;
import com.standup.todo.entity.TeamMember;
import com.standup.todo.repository.TeamMemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class AIService {

    private final TeamMemberRepository teamMemberRepository;

    // 动作关键词，用于识别可能的待办事项
    private static final String[] ACTION_KEYWORDS = {
        "负责", "完成", "实现", "开发", "设计", "编写", "修改", "更新", "修复", "优化",
        "提交", "部署", "测试", "审核", "确认", "跟进", "处理", "解决", "调研", "准备",
        "创建", "搭建", "配置", "整理", "梳理", "沟通", "协调", "推动", "执行", "输出"
    };

    // 优先级关键词
    private static final String[] HIGH_PRIORITY_KEYWORDS = {
        "紧急", "重要", "优先", "尽快", "立即", "马上", "加急", "急", "高优"
    };

    private static final String[] LOW_PRIORITY_KEYWORDS = {
        "不急", "有空", "闲暇", "低优", "后续", "以后", "再说"
    };

    /**
     * 根据输入内容智能识别待办事项
     * 支持任意格式的会议纪要
     */
    public AIGenerateResponse generateTodos(String content, String teamId) {
        List<AIGenerateResponse.GeneratedTodo> todos = new ArrayList<>();

        // 获取团队成员列表
        List<TeamMember> members = teamMemberRepository.findByTeamId(teamId);
        List<String> memberIds = members.stream()
                .map(TeamMember::getUserId)
                .collect(Collectors.toList());

        // 智能解析内容
        todos = intelligentParse(content, memberIds);

        // 生成摘要
        String summary = String.format("共识别出 %d 项待办任务", todos.size());

        return AIGenerateResponse.builder()
                .todos(todos)
                .summary(summary)
                .build();
    }

    /**
     * 智能解析会议纪要内容
     */
    private List<AIGenerateResponse.GeneratedTodo> intelligentParse(String content, List<String> memberIds) {
        List<AIGenerateResponse.GeneratedTodo> todos = new ArrayList<>();

        if (content == null || content.trim().isEmpty()) {
            return todos;
        }

        // 方式1：按行分割，逐行分析
        String[] lines = content.split("\n");
        for (String line : lines) {
            line = line.trim();
            if (line.isEmpty() || line.length() < 4) {
                continue;
            }

            // 移除列表前缀
            line = line.replaceAll("^[\\d]+[.、)）]\\s*", "");
            line = line.replaceAll("^[-*•·]\\s*", "");

            if (line.isEmpty()) {
                continue;
            }

            // 检查是否包含动作关键词
            if (containsActionKeyword(line)) {
                String priority = detectPriority(line);
                String assignee = detectAssignee(line, memberIds);
                String cleanedContent = cleanContent(line);

                if (!cleanedContent.isEmpty() && cleanedContent.length() >= 2) {
                    todos.add(AIGenerateResponse.GeneratedTodo.builder()
                            .content(cleanedContent)
                            .priority(priority)
                            .suggestedAssignee(assignee)
                            .build());
                }
            }
        }

        // 方式2：如果按行分割没有找到足够结果，尝试按句子分割
        if (todos.size() < 2) {
            todos.addAll(parseBySentence(content, memberIds));
        }

        // 去重
        todos = deduplicateTodos(todos);

        return todos;
    }

    /**
     * 按句子解析，用于处理长段落文本
     */
    private List<AIGenerateResponse.GeneratedTodo> parseBySentence(String content, List<String> memberIds) {
        List<AIGenerateResponse.GeneratedTodo> todos = new ArrayList<>();

        // 按句号、分号、换行分割
        String[] sentences = content.split("[。；;！！\n]+");

        for (String sentence : sentences) {
            sentence = sentence.trim();
            if (sentence.isEmpty() || sentence.length() < 6) {
                continue;
            }

            // 检查是否包含动作关键词
            if (containsActionKeyword(sentence)) {
                String priority = detectPriority(sentence);
                String assignee = detectAssignee(sentence, memberIds);
                String cleanedContent = cleanContent(sentence);

                if (!cleanedContent.isEmpty() && cleanedContent.length() >= 4) {
                    todos.add(AIGenerateResponse.GeneratedTodo.builder()
                            .content(cleanedContent)
                            .priority(priority)
                            .suggestedAssignee(assignee)
                            .build());
                }
            }
        }

        return todos;
    }

    /**
     * 检查是否包含动作关键词
     */
    private boolean containsActionKeyword(String text) {
        for (String keyword : ACTION_KEYWORDS) {
            if (text.contains(keyword)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 检测优先级
     */
    private String detectPriority(String text) {
        // 显式优先级标记
        if (text.contains("!!!")) return "LOW";
        if (text.contains("!!")) return "MEDIUM";
        if (text.contains("!")) return "HIGH";

        // [] 或 () 标记
        Pattern bracketPattern = Pattern.compile("[\\[\\(](高|中|低|HIGH|MEDIUM|LOW)[\\]\\)]");
        Matcher bracketMatcher = bracketPattern.matcher(text);
        if (bracketMatcher.find()) {
            String p = bracketMatcher.group(1);
            if (p.equals("高") || p.equals("HIGH")) return "HIGH";
            if (p.equals("低") || p.equals("LOW")) return "LOW";
            return "MEDIUM";
        }

        // 基于关键词推断优先级
        for (String keyword : HIGH_PRIORITY_KEYWORDS) {
            if (text.contains(keyword)) return "HIGH";
        }
        for (String keyword : LOW_PRIORITY_KEYWORDS) {
            if (text.contains(keyword)) return "LOW";
        }

        return "MEDIUM";
    }

    /**
     * 检测责任人
     */
    private String detectAssignee(String text, List<String> memberIds) {
        // 显式 @ 标记
        Pattern atPattern = Pattern.compile("@(\\S+)");
        Matcher atMatcher = atPattern.matcher(text);
        if (atMatcher.find()) {
            String assignee = atMatcher.group(1);
            if (memberIds.contains(assignee)) {
                return assignee;
            }
        }

        // 检查文本中是否直接提到团队成员ID
        for (String memberId : memberIds) {
            if (text.contains(memberId)) {
                return memberId;
            }
        }

        return null;
    }

    /**
     * 清理内容，移除标记符号
     */
    private String cleanContent(String text) {
        // 移除优先级标记
        text = text.replaceAll("!!!", "");
        text = text.replaceAll("!!", "");
        text = text.replaceAll("\\[(高|中|低|HIGH|MEDIUM|LOW)\\]", "");
        text = text.replaceAll("\\((高|中|低|HIGH|MEDIUM|LOW)\\)", "");

        // 移除 @ 标记
        text = text.replaceAll("@\\S+", "");

        // 移除多余空格
        text = text.replaceAll("\\s+", " ").trim();

        return text;
    }

    /**
     * 去重
     */
    private List<AIGenerateResponse.GeneratedTodo> deduplicateTodos(List<AIGenerateResponse.GeneratedTodo> todos) {
        List<AIGenerateResponse.GeneratedTodo> uniqueTodos = new ArrayList<>();
        List<String> seenContents = new ArrayList<>();

        for (AIGenerateResponse.GeneratedTodo todo : todos) {
            String normalizedContent = todo.getContent().replaceAll("\\s+", "");
            if (!seenContents.contains(normalizedContent)) {
                seenContents.add(normalizedContent);
                uniqueTodos.add(todo);
            }
        }

        return uniqueTodos;
    }
}
