package com.standupsync.dto;

import java.util.List;
import java.util.Map;

/**
 * Comprehensive dashboard summary for a team/sprint.
 */
public class DashboardSummary {

    // Sprint info
    private Long teamId;
    private String teamName;
    private Integer sprintNo;

    // Meeting stats
    private int totalMeetings;
    private int completedMeetings;
    private int activeMeetings;

    // Speech / attendance stats
    private int totalSpeakers;
    private int totalSpeeches;
    private Map<String, Integer> speakerSpeechCount; // displayName -> count

    // Action item stats
    private int totalActionItems;
    private int completedActionItems;
    private int inProgressActionItems;
    private int todoActionItems;

    // Priority distribution
    private int highPriorityItems;
    private int mediumPriorityItems;
    private int lowPriorityItems;

    // Blockers
    private List<String> blockers;

    // Completion rate
    private double actionItemCompletionRate;

    public DashboardSummary() {}

    public Long getTeamId() { return teamId; }
    public void setTeamId(Long teamId) { this.teamId = teamId; }
    public String getTeamName() { return teamName; }
    public void setTeamName(String teamName) { this.teamName = teamName; }
    public Integer getSprintNo() { return sprintNo; }
    public void setSprintNo(Integer sprintNo) { this.sprintNo = sprintNo; }
    public int getTotalMeetings() { return totalMeetings; }
    public void setTotalMeetings(int totalMeetings) { this.totalMeetings = totalMeetings; }
    public int getCompletedMeetings() { return completedMeetings; }
    public void setCompletedMeetings(int completedMeetings) { this.completedMeetings = completedMeetings; }
    public int getActiveMeetings() { return activeMeetings; }
    public void setActiveMeetings(int activeMeetings) { this.activeMeetings = activeMeetings; }
    public int getTotalSpeakers() { return totalSpeakers; }
    public void setTotalSpeakers(int totalSpeakers) { this.totalSpeakers = totalSpeakers; }
    public int getTotalSpeeches() { return totalSpeeches; }
    public void setTotalSpeeches(int totalSpeeches) { this.totalSpeeches = totalSpeeches; }
    public Map<String, Integer> getSpeakerSpeechCount() { return speakerSpeechCount; }
    public void setSpeakerSpeechCount(Map<String, Integer> speakerSpeechCount) { this.speakerSpeechCount = speakerSpeechCount; }
    public int getTotalActionItems() { return totalActionItems; }
    public void setTotalActionItems(int totalActionItems) { this.totalActionItems = totalActionItems; }
    public int getCompletedActionItems() { return completedActionItems; }
    public void setCompletedActionItems(int completedActionItems) { this.completedActionItems = completedActionItems; }
    public int getInProgressActionItems() { return inProgressActionItems; }
    public void setInProgressActionItems(int inProgressActionItems) { this.inProgressActionItems = inProgressActionItems; }
    public int getTodoActionItems() { return todoActionItems; }
    public void setTodoActionItems(int todoActionItems) { this.todoActionItems = todoActionItems; }
    public int getHighPriorityItems() { return highPriorityItems; }
    public void setHighPriorityItems(int highPriorityItems) { this.highPriorityItems = highPriorityItems; }
    public int getMediumPriorityItems() { return mediumPriorityItems; }
    public void setMediumPriorityItems(int mediumPriorityItems) { this.mediumPriorityItems = mediumPriorityItems; }
    public int getLowPriorityItems() { return lowPriorityItems; }
    public void setLowPriorityItems(int lowPriorityItems) { this.lowPriorityItems = lowPriorityItems; }
    public List<String> getBlockers() { return blockers; }
    public void setBlockers(List<String> blockers) { this.blockers = blockers; }
    public double getActionItemCompletionRate() { return actionItemCompletionRate; }
    public void setActionItemCompletionRate(double actionItemCompletionRate) { this.actionItemCompletionRate = actionItemCompletionRate; }
}
