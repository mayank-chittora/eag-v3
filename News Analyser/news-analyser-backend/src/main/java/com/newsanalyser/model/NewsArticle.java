package com.newsanalyser.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

@Entity
@Table(name = "news_articles",
       indexes = {
           @Index(name = "idx_articles_published_at", columnList = "published_at"),
           @Index(name = "idx_articles_sentiment", columnList = "sentiment"),
           @Index(name = "idx_articles_source", columnList = "source_name"),
           @Index(name = "idx_articles_scraped_at", columnList = "scraped_at")
       })
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NewsArticle {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 1000)
    private String url;

    @Column(nullable = false, length = 500)
    private String headline;

    @Column(columnDefinition = "TEXT")
    private String summary;

    @Column(nullable = false, length = 200)
    private String sourceName;

    @Column(length = 500)
    private String imageUrl;

    @Column(name = "published_at", nullable = false)
    private LocalDateTime publishedAt;

    @Column(name = "scraped_at", nullable = false)
    private LocalDateTime scrapedAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private SentimentLabel sentiment;

    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
        name = "article_categories",
        joinColumns = @JoinColumn(name = "article_id"),
        inverseJoinColumns = @JoinColumn(name = "category_id")
    )
    @Builder.Default
    private Set<Category> categories = new HashSet<>();
}
