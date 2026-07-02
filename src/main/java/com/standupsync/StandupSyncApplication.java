package com.standupsync;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@MapperScan("com.standupsync.mapper")
@EnableScheduling
public class StandupSyncApplication {
    public static void main(String[] args) {
        SpringApplication.run(StandupSyncApplication.class, args);
    }
}
