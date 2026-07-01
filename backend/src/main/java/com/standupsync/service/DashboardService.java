package com.standupsync.service;

import com.standupsync.model.*;
import com.standupsync.repository.*;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

@Service
public class DashboardService {

    private final MeetingRepository meetingRepo;
    private final MeetingParticipantRepository participantRepo;
    private final MeetingSpeechRepository speechRepo;
    private final ActionItemRepository itemRepo;
    private final TeamMemberRepository memberRepo;

    public DashboardService(MeetingRepository meetingRepo, MeetingParticipantRepository participantRepo,
                            MeetingSpeechRepository speechRepo, ActionItemRepository itemRepo,
                            TeamMemberRepository memberRepo) {
        this.meetingRepo = meetingRepo;
        this.participantRepo = participantRepo;
        this.speechRepo = speechRepo;
        this.itemRepo = itemRepo;
        this.memberRepo = memberRepo;
    }

    public Map<String, Object> computeSummary(Long teamId, String sprintNo,
                                               LocalDate dateFrom, LocalDate dateTo) {
        List<Meeting> meetings = meetingRepo.findByTeamIdOrderByCreatedAtDesc(teamId);
        meetings = filterMeetings(meetings, sprintNo, dateFrom, dateTo);
        List<ActionItem> items = itemRepo.findByTeamId(teamId);

        long totalMeetings = meetings.size();
        long endedMeetings = meetings.stream().filter(m -> m.getStatus() == Meeting.MeetingStatus.ENDED).count();

        double avgAttendance = 0;
        long totalBlockers = 0;
        for (Meeting m : meetings) {
            List<MeetingParticipant> parts = participantRepo.findByMeetingIdOrderBySpeechOrderAsc(m.getId());
            if (!parts.isEmpty()) {
                avgAttendance += (double) parts.stream().filter(p -> p.getHasSpoken()).count() / parts.size();
            }
            List<MeetingSpeech> speeches = speechRepo.findByMeetingIdOrderByCreatedAtAsc(m.getId());
            for (MeetingSpeech s : speeches) {
                if (s.getBlockers() != null && !s.getBlockers().isBlank()) totalBlockers++;
            }
        }
        if (!meetings.isEmpty()) avgAttendance /= meetings.size();

        long totalItems = items.size();
        long completedItems = items.stream().filter(i -> i.getStatus() == ActionItem.ActionItemStatus.DONE).count();
        double completionRate = totalItems > 0 ? (double) completedItems / totalItems : 0;

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("totalMeetings", totalMeetings);
        result.put("endedMeetings", endedMeetings);
        result.put("avgAttendanceRate", Math.round(avgAttendance * 100.0) / 100.0);
        result.put("completionRate", Math.round(completionRate * 100.0) / 100.0);
        result.put("activeBlockers", totalBlockers);
        result.put("totalActionItems", totalItems);
        result.put("completedItems", completedItems);
        return result;
    }

    public List<Map<String, Object>> computeAttendanceTrend(Long teamId, int limit,
                                                             String userId) {
        List<Meeting> meetings = meetingRepo.findByTeamIdOrderByCreatedAtDesc(teamId);
        if (meetings.size() > limit) meetings = meetings.subList(0, limit);
        Collections.reverse(meetings);

        List<Map<String, Object>> trend = new ArrayList<>();
        for (Meeting m : meetings) {
            List<MeetingParticipant> parts = participantRepo.findByMeetingIdOrderBySpeechOrderAsc(m.getId());
            if (userId != null) {
                parts = parts.stream().filter(p -> userId.equals(p.getUserId())).toList();
            }
            long attended = parts.stream().filter(p -> p.getHasSpoken()).count();
            double rate = parts.isEmpty() ? 0 : (double) attended / parts.size();
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", m.getCreatedAt().toLocalDate().toString());
            point.put("attended", attended);
            point.put("total", parts.size());
            point.put("rate", Math.round(rate * 100.0) / 100.0);
            trend.add(point);
        }
        return trend;
    }

    public List<Map<String, Object>> computeCompletionTrend(Long teamId, int limit,
                                                             String userId) {
        List<Meeting> meetings = meetingRepo.findByTeamIdOrderByCreatedAtDesc(teamId);
        if (meetings.size() > limit) meetings = meetings.subList(0, limit);
        Collections.reverse(meetings);

        List<Map<String, Object>> trend = new ArrayList<>();
        for (Meeting m : meetings) {
            List<ActionItem> items = itemRepo.findByMeetingId(m.getId());
            if (userId != null) {
                items = items.stream().filter(i ->
                    i.getAssignee() != null && userId.equals(i.getAssignee().getId())).toList();
            }
            long done = items.stream().filter(i -> i.getStatus() == ActionItem.ActionItemStatus.DONE).count();
            double rate = items.isEmpty() ? 0 : (double) done / items.size();
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", m.getCreatedAt().toLocalDate().toString());
            point.put("total", items.size());
            point.put("completed", done);
            point.put("rate", Math.round(rate * 100.0) / 100.0);
            trend.add(point);
        }
        return trend;
    }

    public List<Map<String, Object>> computeCompletionTrendDaily(Long teamId, int days) {
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(days);
        List<ActionItem> allItems = itemRepo.findByTeamId(teamId);
        List<Map<String, Object>> result = new ArrayList<>();
        LocalDate current = startDate;
        while (!current.isAfter(endDate)) {
            final LocalDate dayStart = current;
            final LocalDate dayEnd = current.plusDays(1);
            long created = allItems.stream()
                    .filter(i -> i.getCreatedAt() != null)
                    .filter(i -> {
                        LocalDate d = i.getCreatedAt().toLocalDate();
                        return !d.isBefore(dayStart) && d.isBefore(dayEnd);
                    }).count();
            long completed = allItems.stream()
                    .filter(i -> i.getCompletedAt() != null)
                    .filter(i -> {
                        LocalDate d = i.getCompletedAt().toLocalDate();
                        return !d.isBefore(dayStart) && d.isBefore(dayEnd);
                    }).count();
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", dayStart.toString());
            point.put("totalCreated", created);
            point.put("totalCompleted", completed);
            result.add(point);
            current = current.plusDays(1);
        }
        return result;
    }

    public List<Map<String, Object>> computeBlockerDistribution(Long teamId, String filterType) {
        List<Map<String, Object>> distribution = new ArrayList<>();
        Map<String, String> colors = Map.of(
            "tech", "#1890FF", "resource", "#F5A623",
            "communication", "#7B7B7B", "other", "#D0D0D0"
        );
        Map<String, String> labels = Map.of(
            "tech", "技术问题", "resource", "资源问题",
            "communication", "沟通问题", "other", "其他"
        );
        List<Meeting> meetings = meetingRepo.findByTeamIdOrderByCreatedAtDesc(teamId);
        Map<String, Long> counts = new LinkedHashMap<>();
        counts.put("tech", 0L); counts.put("resource", 0L);
        counts.put("communication", 0L); counts.put("other", 0L);

        for (Meeting m : meetings) {
            List<MeetingSpeech> speeches = speechRepo.findByMeetingIdOrderByCreatedAtAsc(m.getId());
            for (MeetingSpeech s : speeches) {
                if (s.getBlockers() == null || s.getBlockers().isBlank()) continue;
                String cat = categorize(s.getBlockers());
                if (filterType != null && !filterType.equals(cat)) continue;
                counts.merge(cat, 1L, Long::sum);
            }
        }

        for (Map.Entry<String, Long> e : counts.entrySet()) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("type", e.getKey());
            item.put("label", labels.getOrDefault(e.getKey(), e.getKey()));
            item.put("count", e.getValue());
            item.put("color", colors.getOrDefault(e.getKey(), "#CCC"));
            distribution.add(item);
        }
        return distribution;
    }

    public List<Map<String, Object>> computeMemberRanking(Long teamId, String sortBy) {
        List<TeamMember> members = memberRepo.findByTeamId(teamId);
        List<ActionItem> items = itemRepo.findByTeamId(teamId);
        List<Map<String, Object>> ranking = new ArrayList<>();

        for (TeamMember member : members) {
            List<ActionItem> userItems = items.stream()
                .filter(i -> i.getAssignee() != null && member.getUserId().equals(i.getAssignee().getId()))
                .toList();
            long total = userItems.size();
            long done = userItems.stream().filter(i -> i.getStatus() == ActionItem.ActionItemStatus.DONE).count();
            double rate = total > 0 ? (double) done / total : 0;

            Map<String, Object> rank = new LinkedHashMap<>();
            rank.put("userId", member.getUserId());
            rank.put("totalItems", total);
            rank.put("completedItems", done);
            rank.put("completionRate", Math.round(rate * 100.0) / 100.0);
            ranking.add(rank);
        }
        ranking.sort((a, b) -> Double.compare(
            (double) b.get("completionRate"), (double) a.get("completionRate")));
        for (int i = 0; i < ranking.size(); i++) {
            ranking.get(i).put("rank", i + 1);
        }
        return ranking;
    }

    public String exportMeetingsCsv(Long teamId) {
        List<Meeting> meetings = meetingRepo.findByTeamIdOrderByCreatedAtDesc(teamId);
        StringBuilder sb = new StringBuilder("ID,标题,Sprint,形式,状态,创建时间,结束时间\n");
        for (Meeting m : meetings) {
            sb.append(m.getId()).append(",")
              .append(escapeCsv(m.getTitle())).append(",")
              .append(m.getSprintNo()).append(",")
              .append(m.getFormType()).append(",")
              .append(m.getStatus()).append(",")
              .append(m.getCreatedAt()).append(",")
              .append(m.getEndedAt() != null ? m.getEndedAt() : "").append("\n");
        }
        return sb.toString();
    }

    public String exportActionItemsCsv(Long teamId) {
        List<ActionItem> items = itemRepo.findByTeamId(teamId);
        StringBuilder sb = new StringBuilder("ID,内容,责任人,状态,优先级,创建时间,完成时间\n");
        for (ActionItem i : items) {
            sb.append(i.getId()).append(",")
              .append(escapeCsv(i.getContent())).append(",")
              .append(i.getAssignee() != null ? i.getAssignee().getUsername() : "").append(",")
              .append(i.getStatus()).append(",")
              .append(i.getPriority()).append(",")
              .append(i.getCreatedAt()).append(",")
              .append(i.getCompletedAt() != null ? i.getCompletedAt() : "").append("\n");
        }
        return sb.toString();
    }

    // ── 辅助 ──

    private List<Meeting> filterMeetings(List<Meeting> meetings, String sprintNo,
                                          LocalDate dateFrom, LocalDate dateTo) {
        if (sprintNo != null) {
            int sn = Integer.parseInt(sprintNo);
            meetings = meetings.stream().filter(m -> m.getSprintNo() != null && m.getSprintNo() == sn).toList();
        }
        if (dateFrom != null) {
            meetings = meetings.stream().filter(m ->
                m.getCreatedAt() != null && !m.getCreatedAt().toLocalDate().isBefore(dateFrom)).toList();
        }
        if (dateTo != null) {
            meetings = meetings.stream().filter(m ->
                m.getCreatedAt() != null && !m.getCreatedAt().toLocalDate().isAfter(dateTo)).toList();
        }
        return meetings;
    }

    private String categorize(String blocker) {
        String t = blocker.toLowerCase();
        if (t.contains("环境") || t.contains("数据库") || t.contains("服务器") || t.contains("bug") || t.contains("代码") || t.contains("技术")) return "tech";
        if (t.contains("资源") || t.contains("人力") || t.contains("排期") || t.contains("人手")) return "resource";
        if (t.contains("沟通") || t.contains("需求") || t.contains("不清楚") || t.contains("等待")) return "communication";
        return "other";
    }

    private String escapeCsv(String s) {
        if (s == null) return "";
        if (s.contains(",") || s.contains("\"") || s.contains("\n")) {
            return "\"" + s.replace("\"", "\"\"") + "\"";
        }
        return s;
    }
}
