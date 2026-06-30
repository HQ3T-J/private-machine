package com.standupsync.dto;

/**
 * 发言提交 DTO — 结构化三段式
 */
public class SubmitSpeechDTO {

    private String yesterdayWork;
    private String todayPlan;
    private String blockers;
    private String inputMethod = "TEXT";

    public SubmitSpeechDTO() {}

    public String getYesterdayWork() { return yesterdayWork; }
    public void setYesterdayWork(String yesterdayWork) { this.yesterdayWork = yesterdayWork; }

    public String getTodayPlan() { return todayPlan; }
    public void setTodayPlan(String todayPlan) { this.todayPlan = todayPlan; }

    public String getBlockers() { return blockers; }
    public void setBlockers(String blockers) { this.blockers = blockers; }

    public String getInputMethod() { return inputMethod; }
    public void setInputMethod(String inputMethod) { this.inputMethod = inputMethod; }
}
