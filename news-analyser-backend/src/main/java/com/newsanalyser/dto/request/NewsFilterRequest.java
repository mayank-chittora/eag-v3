package com.newsanalyser.dto.request;

import com.newsanalyser.model.SentimentLabel;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

import java.time.LocalDate;
import java.util.List;

import org.springframework.format.annotation.DateTimeFormat;

@Data
public class NewsFilterRequest {
    
    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
    private LocalDate date;

    private List<String> categories;

    private SentimentLabel sentiment;

    private List<String> sources;

    @Min(0)
    private int page = 0;

    @Min(1)
    @Max(50)
    private int pageSize = 20;
}
