package com.standupsync.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("standup_meeting")
public class StandupMeeting {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long teamId;
    private String sprint;
    private LocalDate meetingDate;
    private String mode;
    private String status;
    private Integer countdownSeconds;
    private LocalDateTime countdownEndAt;
    private Integer isArchived;
    private LocalDateTime archivedAt;
    private Long createdBy;
    @TableLogic
    private Integer deleted;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
