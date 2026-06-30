package com.standupsync.dto;

import java.util.Map;

/**
 * DTO for the AI analysis pipeline result.
 */
public class AnalysisResult {

    /** Step 1: Mapping of speaker labels to identified user IDs/names */
    private Map<String, String> speakerIdentification;

    /** Step 2: Per-person structured meeting notes */
    private Map<String, String> personSummaries;

    /** Step 3: Aggregate meeting summary */
    private String meetingSummary;

    /** Step 3: Extracted action items as JSON array string */
    private String actionItemsJson;

    public AnalysisResult() {}

    public AnalysisResult(Map<String, String> speakerIdentification,
                          Map<String, String> personSummaries,
                          String meetingSummary,
                          String actionItemsJson) {
        this.speakerIdentification = speakerIdentification;
        this.personSummaries = personSummaries;
        this.meetingSummary = meetingSummary;
        this.actionItemsJson = actionItemsJson;
    }

    public Map<String, String> getSpeakerIdentification() { return speakerIdentification; }
    public void setSpeakerIdentification(Map<String, String> speakerIdentification) { this.speakerIdentification = speakerIdentification; }
    public Map<String, String> getPersonSummaries() { return personSummaries; }
    public void setPersonSummaries(Map<String, String> personSummaries) { this.personSummaries = personSummaries; }
    public String getMeetingSummary() { return meetingSummary; }
    public void setMeetingSummary(String meetingSummary) { this.meetingSummary = meetingSummary; }
    public String getActionItemsJson() { return actionItemsJson; }
    public void setActionItemsJson(String actionItemsJson) { this.actionItemsJson = actionItemsJson; }
}
