package com.newsanalyser.repository;

import com.newsanalyser.model.NewsArticle;
import com.newsanalyser.model.SentimentLabel;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface NewsArticleRepository extends JpaRepository<NewsArticle, Long>,
        JpaSpecificationExecutor<NewsArticle> {

    boolean existsByUrl(String url);

    Optional<NewsArticle> findByUrl(String url);

    @EntityGraph(attributePaths = "categories")
    @Query("""
        SELECT a FROM NewsArticle a
        WHERE a.publishedAt BETWEEN :start AND :end
        ORDER BY a.publishedAt DESC
        """)
    Page<NewsArticle> findByPublishedAtBetween(
        @Param("start") LocalDateTime start,
        @Param("end") LocalDateTime end,
        Pageable pageable
    );

    @EntityGraph(attributePaths = "categories")
    @Query("""
        SELECT DISTINCT a FROM NewsArticle a
        JOIN a.categories c
        WHERE c.slug IN :categorySlugs
          AND a.publishedAt BETWEEN :start AND :end
        ORDER BY a.publishedAt DESC
        """)
    Page<NewsArticle> findByCategorySlugsAndDateRange(
        @Param("categorySlugs") List<String> categorySlugs,
        @Param("start") LocalDateTime start,
        @Param("end") LocalDateTime end,
        Pageable pageable
    );

    @Query("""
        SELECT DISTINCT a FROM NewsArticle a
        JOIN a.categories c
        WHERE c.slug IN :categorySlugs
          AND a.publishedAt >= :since
        ORDER BY a.publishedAt DESC
        """)
    List<NewsArticle> findRecentByCategorySlugs(
        @Param("categorySlugs") List<String> categorySlugs,
        @Param("since") LocalDateTime since,
        Pageable pageable
    );

    @Query("SELECT DISTINCT a.sourceName FROM NewsArticle a ORDER BY a.sourceName")
    List<String> findDistinctSourceNames();

    long countByScrapedAtAfter(LocalDateTime since);

    @EntityGraph(attributePaths = "categories")
    @Query("""
        SELECT a FROM NewsArticle a
        WHERE a.scrapedAt BETWEEN :start AND :end
        ORDER BY a.scrapedAt DESC
        """)
    Page<NewsArticle> findByScrapedAtBetween(
        @Param("start") LocalDateTime start,
        @Param("end") LocalDateTime end,
        Pageable pageable
    );
}
