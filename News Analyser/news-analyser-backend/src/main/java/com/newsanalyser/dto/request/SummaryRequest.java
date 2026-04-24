package com.newsanalyser.dto.request;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

import java.util.List;

@Data
public class SummaryRequest {

    @NotEmpty(message = "At least one category slug is required")
    private List<String> categories;

    @NotNull(message = "Date is required")
    @Pattern(regexp = "\\d{4}-\\d{2}-\\d{2}", message = "Date must be YYYY-MM-DD")
    private String date;
}
