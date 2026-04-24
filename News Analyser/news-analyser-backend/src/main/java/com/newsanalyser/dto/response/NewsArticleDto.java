package com.newsanalyser.dto.response;

import com.newsanalyser.model.SentimentLabel;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Set;

@Data
@Builder
public class NewsArticleDto {
    private Long id;
    private String url;
    private String headline;
    private String summary;
    private String sourceName;
    private String imageUrl;
    private LocalDateTime publishedAt;
    private SentimentLabel sentiment;
    private Set<CategoryDto> categories;
}
