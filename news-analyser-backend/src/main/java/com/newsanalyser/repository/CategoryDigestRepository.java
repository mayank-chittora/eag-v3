package com.newsanalyser.repository;

import com.newsanalyser.model.CategoryDigest;
import com.newsanalyser.model.SentimentLabel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface CategoryDigestRepository extends JpaRepository<CategoryDigest, Long> {

    List<CategoryDigest> findByDateAndCategorySlugIn(LocalDate date, List<String> categorySlugs);

    List<CategoryDigest> findByDate(LocalDate date);

    Optional<CategoryDigest> findByDateAndCategorySlugAndSentiment(
            LocalDate date, String categorySlug, SentimentLabel sentiment);
}
