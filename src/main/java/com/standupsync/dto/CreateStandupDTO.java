package com.standupsync.dto;
import lombok.Data;
import java.util.List;
@Data
public class CreateStandupDTO {
    private Long teamId;
    private String sprint;
    private String mode;
    private List<Long> memberIds;
}
