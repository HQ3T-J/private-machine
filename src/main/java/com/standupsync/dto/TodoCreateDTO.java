package com.standupsync.dto;
import lombok.Data;
import java.time.LocalDateTime;
@Data
public class TodoCreateDTO {
    private Long teamId;
    private String content;
    private Long assigneeId;
    private String priority;
    private LocalDateTime deadline;
    private Long sourceStandupId;
}
