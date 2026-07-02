package com.standupsync.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public class RegisterRequest {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度需在3-50之间")
    @Pattern(regexp = ".*[a-zA-Z].*", message = "用户名需包含字母")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Size(min = 4, max = 100, message = "密码长度需在4-100之间")
    private String password;

    @Size(max = 50, message = "昵称最长50字符")
    private String displayName;

    public RegisterRequest() {
    }

    public RegisterRequest(String username, String password, String displayName) {
        this.username = username;
        this.password = password;
        this.displayName = displayName;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }
}
