package com.newsanalyser.service;

import com.newsanalyser.dto.response.CategoryDto;
import com.newsanalyser.repository.CategoryRepository;
import com.newsanalyser.repository.NewsArticleRepository;
import com.newsanalyser.util.AppConstants;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class CategoryServiceImpl implements CategoryService {

    private final CategoryRepository categoryRepository;
    private final NewsArticleRepository articleRepository;

    @Override
    @Cacheable(AppConstants.CACHE_CATEGORIES)
    public List<CategoryDto> getAllCategories() {
        return categoryRepository.findAllByOrderByNameAsc().stream()
                .map(c -> CategoryDto.builder()
                        .id(c.getId())
                        .name(c.getName())
                        .slug(c.getSlug())
                        .accentColor(c.getAccentColor())
                        .lightBgColor(c.getLightBgColor())
                        .build())
                .toList();
    }

    @Override
    @Cacheable(AppConstants.CACHE_SOURCES)
    public List<String> getAllSourceNames() {
        List<String> dbSources = articleRepository.findDistinctSourceNames();
        return dbSources.isEmpty() ? AppConstants.SUPPORTED_SOURCES : dbSources;
    }
}
