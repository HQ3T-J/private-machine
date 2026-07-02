package com.standup.todo.repository;

import com.standup.todo.entity.Todo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TodoRepository extends JpaRepository<Todo, Long> {

    List<Todo> findByTeamIdAndIsDeletedFalse(String teamId);

    List<Todo> findByAssigneeIdAndIsDeletedFalse(String assigneeId);

    List<Todo> findByTeamIdAndStatusAndIsDeletedFalse(String teamId, Todo.Status status);

    List<Todo> findByAssigneeIdAndStatusAndIsDeletedFalse(String assigneeId, Todo.Status status);

    long countByTeamIdAndIsDeletedFalse(String teamId);

    long countByTeamIdAndStatusAndIsDeletedFalse(String teamId, Todo.Status status);

    long countByAssigneeIdAndIsDeletedFalse(String assigneeId);

    long countByAssigneeIdAndStatusAndIsDeletedFalse(String assigneeId, Todo.Status status);

    List<Todo> findByTeamIdAndTransferStatusAndIsDeletedFalse(String teamId, Todo.TransferStatus transferStatus);

    List<Todo> findByTeamIdAndTransferStatusInAndIsDeletedFalse(String teamId, List<Todo.TransferStatus> transferStatuses);
}
