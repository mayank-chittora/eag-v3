package com.newsanalyser.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "category_digests",
       uniqueConstraints = @UniqueConstraint(
           name = "uq_digest",
           columnNames = {"date", "category_slug", "sentiment"}
       ))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CategoryDigest {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private LocalDate date;

    @Column(name = "category_slug", nullable = false, length = 100)
    private String categorySlug;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private SentimentLabel sentiment;

    @Column(name = "digest_text", nullable = false, columnDefinition = "TEXT")
    private String digestText;

    @Column(name = "generated_at", nullable = false)
    private LocalDateTime generatedAt;
}
