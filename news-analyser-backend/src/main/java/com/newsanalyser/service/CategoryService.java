package com.newsanalyser.service;

import com.newsanalyser.dto.response.CategoryDto;

import java.util.List;

public interface CategoryService {
    List<CategoryDto> getAllCategories();
    List<String> getAllSourceNames();
}
