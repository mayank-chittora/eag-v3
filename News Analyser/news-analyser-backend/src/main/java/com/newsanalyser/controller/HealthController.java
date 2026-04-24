package com.newsanalyser.controller;

import com.newsanalyser.dto.response.ApiResponse;
import com.newsanalyser.repository.NewsArticleRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/health")
@RequiredArgsConstructor
@Tag(name = "Health", description = "Service health check")
public class HealthController {

    private final NewsArticleRepository articleRepository;

    @GetMapping
    @Operation(summary = "Get service health status")
    public ResponseEntity<ApiResponse<Map<String, Object>>> health() {
        long recentCount = articleRepository.countByScrapedAtAfter(LocalDateTime.now().minusHours(1));
        return ResponseEntity.ok(ApiResponse.success(Map.of(
            "status", "UP",
            "timestamp", LocalDateTime.now().toString(),
            "articlesLastHour", recentCount
        )));
    }
}
