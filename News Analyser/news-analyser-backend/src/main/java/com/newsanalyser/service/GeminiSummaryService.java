package com.newsanalyser.service;

import com.newsanalyser.dto.request.SummaryRequest;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface GeminiSummaryService {
    SseEmitter generateSummary(SummaryRequest request);
}
