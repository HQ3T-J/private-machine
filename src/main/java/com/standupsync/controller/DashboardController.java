package com.standupsync.controller;

import com.standupsync.dto.Result;
import com.standupsync.service.DashboardService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/kpi")
    public Result<?> kpi(@RequestParam Long teamId) {
        return dashboardService.getKpiData(teamId);
    }

    @GetMapping("/trends")
    public Result<?> trends(@RequestParam Long teamId) {
        return dashboardService.getTrendData(teamId);
    }

    @GetMapping("/ranking")
    public Result<?> ranking(@RequestParam Long teamId) {
        return dashboardService.getMemberRanking(teamId);
    }
}
