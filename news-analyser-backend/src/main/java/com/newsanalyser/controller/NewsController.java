package com.newsanalyser.controller;

import com.newsanalyser.dto.request.NewsFilterRequest;
import com.newsanalyser.dto.response.ApiResponse;
import com.newsanalyser.dto.response.NewsArticleDto;
import com.newsanalyser.service.NewsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/news")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "News", description = "News feed endpoints")
public class NewsController {

    private final NewsService newsService;

    @GetMapping
    @Operation(summary = "Get paginated news feed with optional filters")
    public ResponseEntity<ApiResponse<List<NewsArticleDto>>> getNews(
            @Valid @ModelAttribute NewsFilterRequest filter) {
        log.debug("GET /api/v1/news filter={}", filter);
        return ResponseEntity.ok(newsService.getNews(filter));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get a single article by ID")
    public ResponseEntity<ApiResponse<NewsArticleDto>> getArticle(@PathVariable Long id) {
        log.debug("GET /api/v1/news/{}", id);
        return ResponseEntity.ok(ApiResponse.success(newsService.getArticleById(id)));
    }
}
