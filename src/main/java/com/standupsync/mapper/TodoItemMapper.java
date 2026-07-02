package com.standupsync.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.standupsync.entity.TodoItem;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;
import java.util.List;

@Mapper
public interface TodoItemMapper extends BaseMapper<TodoItem> {

    @Select("SELECT * FROM todo_item WHERE assignee_id = #{userId} AND status IN ('pending','in_progress') AND deleted = 0 ORDER BY deadline ASC")
    List<TodoItem> findUnfinishedByUser(Long userId);

    @Select("SELECT * FROM todo_item WHERE team_id = #{teamId} AND deleted = 0 ORDER BY create_time DESC")
    List<TodoItem> findByTeam(Long teamId);

    @Update("UPDATE todo_item SET is_overdue = 1 WHERE deadline < NOW() AND status IN ('pending','in_progress') AND is_overdue = 0 AND deleted = 0")
    int markOverdue();
}
