package com.standupsync.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("standup_action_item")
public class StandupActionItem {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long standupId;
    private Long assigneeId;
    private String content;
    private String priority;
    private LocalDateTime deadline;
    private Integer isTodoGenerated;
    private Long todoId;
    private Integer sortOrder;
    @TableLogic
    private Integer deleted;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
