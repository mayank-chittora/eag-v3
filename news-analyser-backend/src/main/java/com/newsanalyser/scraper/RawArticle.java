package com.newsanalyser.scraper;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
public class RawArticle {
    private String url;
    private String headline;
    private String summary;
    private String sourceName;
    private String imageUrl;
    private LocalDateTime publishedAt;
    private List<String> categoryHints; // keyword hints for category assignment
}
