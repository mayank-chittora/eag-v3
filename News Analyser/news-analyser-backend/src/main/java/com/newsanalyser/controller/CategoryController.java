package com.newsanalyser.controller;

import com.newsanalyser.dto.response.ApiResponse;
import com.newsanalyser.dto.response.CategoryDto;
import com.newsanalyser.service.CategoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/categories")
@RequiredArgsConstructor
@Tag(name = "Categories", description = "Interest category endpoints")
public class CategoryController {

    private final CategoryService categoryService;

    @GetMapping
    @Operation(summary = "Get all available interest categories")
    public ResponseEntity<ApiResponse<List<CategoryDto>>> getCategories() {
        return ResponseEntity.ok(ApiResponse.success(categoryService.getAllCategories()));
    }

    @GetMapping("/sources")
    @Operation(summary = "Get all available news sources")
    public ResponseEntity<ApiResponse<List<String>>> getSources() {
        return ResponseEntity.ok(ApiResponse.success(categoryService.getAllSourceNames()));
    }
}
