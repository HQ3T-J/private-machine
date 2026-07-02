package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.service.TeamService;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/teams")
public class TeamController {

    private final TeamService teamService;

    public TeamController(TeamService teamService) {
        this.teamService = teamService;
    }

    @PostMapping
    public ApiResponse<?> createTeam(@RequestAttribute("userId") String userId,
                                      @RequestBody Map<String, String> body) {
        return teamService.createTeam(userId, body.getOrDefault("name", ""));
    }

    @GetMapping
    public ApiResponse<?> listTeams(@RequestAttribute("userId") String userId) {
        return teamService.listTeams(userId);
    }

    @GetMapping("/{id}")
    public ApiResponse<?> getTeam(@PathVariable Long id) {
        return teamService.getTeam(id);
    }

    @PostMapping("/join")
    public ApiResponse<?> applyToJoin(@RequestAttribute("userId") String userId,
                                       @RequestBody Map<String, String> body) {
        return teamService.applyToJoin(userId, body.getOrDefault("inviteCode", ""));
    }

    @GetMapping("/{id}/applications")
    public ApiResponse<?> getApplications(@RequestAttribute("userId") String userId,
                                           @PathVariable Long id) {
        return teamService.getApplications(userId, id);
    }

    @PostMapping("/{id}/applications/{appId}/approve")
    public ApiResponse<?> approveApplication(@RequestAttribute("userId") String userId,
                                              @PathVariable Long id,
                                              @PathVariable Long appId) {
        return teamService.approveApplication(userId, id, appId);
    }

    @PostMapping("/{id}/applications/{appId}/reject")
    public ApiResponse<?> rejectApplication(@RequestAttribute("userId") String userId,
                                             @PathVariable Long id,
                                             @PathVariable Long appId) {
        return teamService.rejectApplication(userId, id, appId);
    }

    @PutMapping("/{id}/members/{uid}/role")
    public ApiResponse<?> changeRole(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id,
                                      @PathVariable String uid,
                                      @RequestBody Map<String, String> body) {
        return teamService.changeRole(userId, id, uid, body.getOrDefault("role", ""));
    }

    @DeleteMapping("/{id}/members/{uid}")
    public ApiResponse<?> removeMember(@RequestAttribute("userId") String userId,
                                        @PathVariable Long id,
                                        @PathVariable String uid) {
        return teamService.removeMember(userId, id, uid);
    }

    @PutMapping("/{id}")
    public ApiResponse<?> updateName(@RequestAttribute("userId") String userId,
                                      @PathVariable Long id,
                                      @RequestBody Map<String, String> body) {
        return teamService.updateName(userId, id, body.getOrDefault("name", ""));
    }

    @PostMapping("/{id}/invite-code")
    public ApiResponse<?> regenerateCode(@RequestAttribute("userId") String userId,
                                          @PathVariable Long id) {
        return teamService.regenerateCode(userId, id);
    }

    @PostMapping("/{id}/dissolve")
    public ApiResponse<?> dissolve(@RequestAttribute("userId") String userId,
                                    @PathVariable Long id) {
        return teamService.dissolve(userId, id);
    }

    @PostMapping("/{id}/invite")
    public ApiResponse<?> getInviteCode(@PathVariable Long id) {
        return teamService.getInviteCode(id);
    }
}
