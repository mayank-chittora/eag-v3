package com.newsanalyser.service;

import com.newsanalyser.dto.request.NewsFilterRequest;
import com.newsanalyser.dto.response.ApiResponse;
import com.newsanalyser.dto.response.CategoryDto;
import com.newsanalyser.dto.response.NewsArticleDto;
import com.newsanalyser.exception.ResourceNotFoundException;
import com.newsanalyser.model.NewsArticle;
import com.newsanalyser.model.SentimentLabel;
import com.newsanalyser.repository.NewsArticleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import jakarta.persistence.criteria.Join;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class NewsServiceImpl implements NewsService {

    private final NewsArticleRepository articleRepository;

    public NewsArticleRepository getArticleRepository() { return articleRepository; }

    @Override
    @Transactional(readOnly = true)
    public ApiResponse<List<NewsArticleDto>> getNews(NewsFilterRequest filter) {
        log.debug("getNews called with filter={}", filter);
        
        LocalDateTime fromDate = null;
        LocalDateTime toDate = null;
        if (filter.getDate() != null) {
            fromDate = filter.getDate().atStartOfDay();
            toDate = filter.getDate().atTime(java.time.LocalTime.MAX);
        }

        Specification<NewsArticle> spec = buildSpec(filter, fromDate, toDate);
        PageRequest pageable = PageRequest.of(filter.getPage(), filter.getPageSize(),
                Sort.by("publishedAt").descending());

        Page<NewsArticle> page = articleRepository.findAll(spec, pageable);

        List<NewsArticleDto> dtos = page.getContent().stream().map(this::toDto).toList();

        return ApiResponse.success(dtos, ApiResponse.PageMeta.builder()
                .page(page.getNumber())
                .pageSize(page.getSize())
                .total(page.getTotalElements())
                .totalPages(page.getTotalPages())
                .build());
    }

    @Override
    @Transactional(readOnly = true)
    public NewsArticleDto getArticleById(Long id) {
        return articleRepository.findById(id)
                .map(this::toDto)
                .orElseThrow(() -> new ResourceNotFoundException("Article", id));
    }

    Specification<NewsArticle> buildSpec(NewsFilterRequest filter,
                                         LocalDateTime fromDate,
                                         LocalDateTime toDate) {
        return (root, query, cb) -> {
            var predicates = new java.util.ArrayList<jakarta.persistence.criteria.Predicate>();

            // Date range — default last 7 days if not specified
            LocalDateTime start = fromDate != null ? fromDate : LocalDateTime.now().minusDays(7);
            LocalDateTime end   = toDate   != null ? toDate   : LocalDateTime.now();
            predicates.add(cb.between(root.get("publishedAt"), start, end));

            // Sentiment filter
            if (filter.getSentiment() != null) {
                predicates.add(cb.equal(root.get("sentiment"), filter.getSentiment()));
            }

            // Source filter
            if (filter.getSources() != null && !filter.getSources().isEmpty()) {
                predicates.add(root.get("sourceName").in(filter.getSources()));
            }

            // Category filter
            if (filter.getCategories() != null && !filter.getCategories().isEmpty()) {
                Join<Object, Object> catJoin = root.join("categories");
                predicates.add(catJoin.get("slug").in(filter.getCategories()));
                if (query != null) query.distinct(true);
            }

            return cb.and(predicates.toArray(new jakarta.persistence.criteria.Predicate[0]));
        };
    }

    @Override
    @Transactional(readOnly = true)
    public List<NewsArticleDto> getNewsByDateAndCategories(String date, List<String> categorySlugs) {
        LocalDate localDate = LocalDate.parse(date, DateTimeFormatter.ISO_DATE);
        LocalDateTime start = localDate.atStartOfDay();
        LocalDateTime end = localDate.atTime(LocalTime.MAX);
        PageRequest pageable = PageRequest.of(0, 200, Sort.by("publishedAt").descending());
        return articleRepository.findByCategorySlugsAndDateRange(categorySlugs, start, end, pageable)
                .getContent().stream().map(this::toDto).toList();
    }

    public NewsArticleDto toDto(NewsArticle a) {
        return NewsArticleDto.builder()
                .id(a.getId())
                .url(a.getUrl())
                .headline(a.getHeadline())
                .summary(a.getSummary())
                .sourceName(a.getSourceName())
                .imageUrl(a.getImageUrl())
                .publishedAt(a.getPublishedAt())
                .sentiment(a.getSentiment())
                .categories(a.getCategories().stream()
                        .map(c -> CategoryDto.builder()
                                .id(c.getId())
                                .name(c.getName())
                                .slug(c.getSlug())
                                .accentColor(c.getAccentColor())
                                .lightBgColor(c.getLightBgColor())
                                .build())
                        .collect(Collectors.toSet()))
                .build();
    }
}
