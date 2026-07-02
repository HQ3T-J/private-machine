package com.standupsync.config;

import com.standupsync.dto.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(IllegalArgumentException.class)
    public ApiResponse<?> handleIllegalArgument(IllegalArgumentException e) {
        log.warn("参数错误: {}", e.getMessage());
        return ApiResponse.error(400, "参数错误: " + e.getMessage());
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ApiResponse<?> handleMissingParam(MissingServletRequestParameterException e) {
        log.warn("缺少参数: {}", e.getParameterName());
        return ApiResponse.error(400, "缺少必要参数: " + e.getParameterName());
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ApiResponse<?> handleTypeMismatch(MethodArgumentTypeMismatchException e) {
        log.warn("参数类型错误: {} (期望: {})", e.getName(), e.getRequiredType() != null ? e.getRequiredType().getSimpleName() : "?");
        return ApiResponse.error(400, "参数类型错误: " + e.getName());
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ApiResponse<?> handleMalformedBody(HttpMessageNotReadableException e) {
        log.warn("请求体解析失败: {}", e.getMessage());
        return ApiResponse.error(400, "请求体格式错误");
    }

    @ExceptionHandler(Exception.class)
    public ApiResponse<?> handleUnexpected(Exception e) {
        log.error("未处理异常: {}", e.getMessage(), e);
        return ApiResponse.error(500, "服务器内部错误，请查看日志");
    }
}
