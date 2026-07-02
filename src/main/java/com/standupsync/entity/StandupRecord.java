package com.standupsync.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("standup_record")
public class StandupRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long standupId;
    private Long userId;
    private Integer speakOrder;
    private String yesterdayWork;
    private String todayPlan;
    private String blockers;
    private String speakStatus;
    private LocalDateTime submittedAt;
    @TableLogic
    private Integer deleted;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
