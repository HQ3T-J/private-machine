package com.standupsync.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 服务端 AI 配置 — 从 application.yml 读取，用户无需在前端配置。
 *
 * 环境变量覆盖（生产环境推荐）：
 *   AI_PROVIDER=openai
 *   AI_MODEL=gpt-4o
 *   AI_API_KEY=sk-xxx
 *   AI_BASE_URL=https://api.openai.com
 */
@Configuration
@ConfigurationProperties(prefix = "ai")
public class AIServerConfig {

    private String provider = "none";
    private String model = "gpt-4o";
    private String apiKey = "";
    private String baseUrl = "";
    private double temperature = 0.7;
    private int maxTokens = 4096;

    public boolean isEnabled() {
        return provider != null && !provider.equals("none") && apiKey != null && !apiKey.isBlank();
    }

    public String getProvider() { return provider; }
    public void setProvider(String provider) { this.provider = provider; }

    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }

    public String getApiKey() { return apiKey; }
    public void setApiKey(String apiKey) { this.apiKey = apiKey; }

    public String getBaseUrl() { return baseUrl; }
    public void setBaseUrl(String baseUrl) { this.baseUrl = baseUrl; }

    public double getTemperature() { return temperature; }
    public void setTemperature(double temperature) { this.temperature = temperature; }

    public int getMaxTokens() { return maxTokens; }
    public void setMaxTokens(int maxTokens) { this.maxTokens = maxTokens; }
}
