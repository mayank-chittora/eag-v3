package com.newsanalyser.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {

    private T data;
    private PageMeta meta;
    private ApiError error;

    public static <T> ApiResponse<T> success(T data) {
        return ApiResponse.<T>builder().data(data).build();
    }

    public static <T> ApiResponse<T> success(T data, PageMeta meta) {
        return ApiResponse.<T>builder().data(data).meta(meta).build();
    }

    public static <T> ApiResponse<T> error(String code, String message) {
        return ApiResponse.<T>builder()
                .error(ApiError.builder().code(code).message(message).build())
                .build();
    }

    @Data
    @Builder
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class PageMeta {
        private int page;
        private int pageSize;
        private long total;
        private int totalPages;
    }

    @Data
    @Builder
    public static class ApiError {
        private String code;
        private String message;
    }
}
