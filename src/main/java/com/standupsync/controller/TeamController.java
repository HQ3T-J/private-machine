package com.standupsync.controller;

import com.standupsync.dto.Result;
import com.standupsync.service.TeamService;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/teams")
public class TeamController {

    private final TeamService teamService;

    public TeamController(TeamService teamService) {
        this.teamService = teamService;
    }

    @PostMapping
    public Result<?> create(@RequestParam String name, Authentication auth) {
        return teamService.createTeam(name, (Long) auth.getPrincipal());
    }

    @PostMapping("/join")
    public Result<?> join(@RequestParam String inviteCode, Authentication auth) {
        return teamService.applyToJoin(inviteCode, (Long) auth.getPrincipal());
    }

    @GetMapping("/{teamId}/applications")
    public Result<?> applications(@PathVariable Long teamId, Authentication auth) {
        return teamService.getApplications(teamId, (Long) auth.getPrincipal());
    }

    @PostMapping("/{teamId}/applications/{appId}/approve")
    public Result<?> approve(@PathVariable Long teamId, @PathVariable Long appId, Authentication auth) {
        return teamService.approveApplication(teamId, appId, (Long) auth.getPrincipal());
    }

    @PostMapping("/{teamId}/applications/{appId}/reject")
    public Result<?> reject(@PathVariable Long teamId, @PathVariable Long appId, Authentication auth) {
        return teamService.rejectApplication(teamId, appId, (Long) auth.getPrincipal());
    }

    @GetMapping("/{teamId}/members")
    public Result<?> members(@PathVariable Long teamId, Authentication auth) {
        return teamService.getTeamMembers(teamId, (Long) auth.getPrincipal());
    }

    @PutMapping("/{teamId}/members/{memberId}/role")
    public Result<?> changeRole(@PathVariable Long teamId, @PathVariable Long memberId,
                                @RequestParam Integer role, Authentication auth) {
        return teamService.changeRole(teamId, memberId, role, (Long) auth.getPrincipal());
    }

    @DeleteMapping("/{teamId}/members/{memberId}")
    public Result<?> removeMember(@PathVariable Long teamId, @PathVariable Long memberId,
                                  Authentication auth) {
        return teamService.removeMember(teamId, memberId, (Long) auth.getPrincipal());
    }

    @GetMapping("/mine")
    public Result<?> myTeams(Authentication auth) {
        return teamService.getMyTeams((Long) auth.getPrincipal());
    }

    @PostMapping("/{teamId}/invite-code")
    public Result<?> regenerateCode(@PathVariable Long teamId, Authentication auth) {
        return teamService.generateNewInviteCode(teamId, (Long) auth.getPrincipal());
    }

    @PostMapping("/{teamId}/dissolve")
    public Result<?> dissolve(@PathVariable Long teamId, Authentication auth) {
        return teamService.dissolveTeam(teamId, (Long) auth.getPrincipal());
    }

    @PutMapping("/{teamId}")
    public Result<?> updateName(@PathVariable Long teamId, @RequestParam String name, Authentication auth) {
        return teamService.updateTeamName(teamId, name, (Long) auth.getPrincipal());
    }
}
