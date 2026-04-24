package com.newsanalyser.controller;

import com.newsanalyser.dto.request.SummaryRequest;
import com.newsanalyser.service.GeminiSummaryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api/v1/summary")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Summary", description = "AI-powered news summary with streaming SSE")
public class SummaryController {

    private final GeminiSummaryService geminiSummaryService;

    @GetMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "Stream a Gemini-generated news summary via SSE")
    public SseEmitter generateSummary(@Valid @ModelAttribute SummaryRequest request) {
        log.debug("GET /api/v1/summary categories={} date={}", request.getCategories(), request.getDate());
        return geminiSummaryService.generateSummary(request);
    }
}
