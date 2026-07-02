package com.standupsync.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("todo_item")
public class TodoItem {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long teamId;
    private String content;
    private Long assigneeId;
    private Long assignerId;
    private Long sourceStandupId;
    private String priority;
    private String status;
    private LocalDateTime deadline;
    private Integer isOverdue;
    private LocalDateTime completedAt;
    @TableLogic
    private Integer deleted;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
