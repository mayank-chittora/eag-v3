package com.newsanalyser.service;

import com.newsanalyser.dto.request.NewsFilterRequest;
import com.newsanalyser.dto.response.ApiResponse;
import com.newsanalyser.dto.response.NewsArticleDto;

import java.util.List;

public interface NewsService {
    ApiResponse<List<NewsArticleDto>> getNews(NewsFilterRequest filter);
    NewsArticleDto getArticleById(Long id);
    List<NewsArticleDto> getNewsByDateAndCategories(String date, List<String> categorySlugs);
}
