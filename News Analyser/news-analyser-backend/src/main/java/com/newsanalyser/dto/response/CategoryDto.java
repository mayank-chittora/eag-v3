package com.newsanalyser.dto.response;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class CategoryDto {
    private Long id;
    private String name;
    private String slug;
    private String accentColor;
    private String lightBgColor;
}
