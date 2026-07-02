package com.standupsync.controller;

import com.standupsync.dto.ApiResponse;
import com.standupsync.dto.TransferRequest;
import com.standupsync.model.ActionItem;
import com.standupsync.service.TodoTransferService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class TodoTransferController {

    private final TodoTransferService transferService;

    public TodoTransferController(TodoTransferService transferService) {
        this.transferService = transferService;
    }

    @PostMapping("/action-items/{id}/transfer")
    public ApiResponse<ActionItem> transfer(
            @RequestAttribute("userId") String userId,
            @PathVariable Long id,
            @RequestBody TransferRequest req) {
        try {
            ActionItem item = transferService.transferTodo(id, req.getTargetUserId(), req.getReason(), userId);
            return ApiResponse.ok(item);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @PostMapping("/action-items/{id}/approve-transfer")
    public ApiResponse<ActionItem> approveTransfer(
            @RequestAttribute("userId") String userId,
            @PathVariable Long id) {
        try {
            ActionItem item = transferService.approveTransfer(id, userId);
            return ApiResponse.ok(item);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @PostMapping("/action-items/{id}/reject-transfer")
    public ApiResponse<ActionItem> rejectTransfer(
            @RequestAttribute("userId") String userId,
            @PathVariable Long id,
            @RequestBody Map<String, String> body) {
        try {
            String reason = body.get("reason");
            ActionItem item = transferService.rejectTransfer(id, userId, reason);
            return ApiResponse.ok(item);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @PostMapping("/action-items/{id}/cancel-transfer")
    public ApiResponse<Void> cancelTransfer(
            @RequestAttribute("userId") String userId,
            @PathVariable Long id) {
        try {
            transferService.cancelTransfer(id, userId);
            return ApiResponse.ok("已取消", null);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @GetMapping("/action-items/pending-transfers")
    public ApiResponse<List<ActionItem>> pendingTransfers(
            @RequestAttribute("userId") String userId,
            @RequestParam Long teamId) {
        try {
            List<ActionItem> list = transferService.getPendingTransfers(teamId, userId);
            return ApiResponse.ok(list);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @GetMapping("/action-items/reviewed-transfers")
    public ApiResponse<List<ActionItem>> reviewedTransfers(
            @RequestAttribute("userId") String userId,
            @RequestParam Long teamId) {
        try {
            List<ActionItem> list = transferService.getReviewedTransfers(teamId, userId);
            return ApiResponse.ok(list);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }

    @PostMapping("/action-items/{id}/hide-transfer-record")
    public ApiResponse<Void> hideTransferRecord(
            @RequestAttribute("userId") String userId,
            @PathVariable Long id) {
        try {
            transferService.hideTransferRecord(id, userId);
            return ApiResponse.ok("已隐藏", null);
        } catch (RuntimeException e) {
            return ApiResponse.error(500, e.getMessage());
        }
    }
}
