package com.standupsync.mapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.standupsync.entity.TeamMember;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface TeamMemberMapper extends BaseMapper<TeamMember> {
    @Select("SELECT * FROM team_member WHERE id = #{id}")
    TeamMember findByIdIgnoreDelete(@Param("id") Long id);

    @Delete("DELETE FROM team_member WHERE id = #{id}")
    int hardDelete(@Param("id") Long id);
}
