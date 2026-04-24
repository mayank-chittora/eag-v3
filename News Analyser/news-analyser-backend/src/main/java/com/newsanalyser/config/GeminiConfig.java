package com.newsanalyser.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "app.gemini")
@Data
public class GeminiConfig {
    private String apiKey = "";
    private String model = "gemini-2.5-flash-preview-04-17";
    private int maxOutputTokens = 8192;
    private double temperature = 0.3;
}
