package com.newsanalyser.config;

import com.newsanalyser.model.Category;
import com.newsanalyser.repository.CategoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@RequiredArgsConstructor
@Slf4j
public class DataInitializer implements ApplicationRunner {

    private final CategoryRepository categoryRepository;

    private static final List<Object[]> CATEGORIES = List.of(
        new Object[]{"Share Market",         "share-market",         "#F59E0B", "#FFFBEB"},
        new Object[]{"Agriculture Sector",   "agriculture-sector",   "#16A34A", "#DCFCE7"},
        new Object[]{"Manufacturing Sector", "manufacturing-sector", "#D97706", "#FEF3C7"},
        new Object[]{"IT Sector",            "it-sector",            "#6366F1", "#EEF2FF"},
        new Object[]{"Healthcare Sector",    "healthcare-sector",    "#EC4899", "#FDF2F8"},
        new Object[]{"Hospitality Sector",   "hospitality-sector",   "#F97316", "#FFF7ED"},
        new Object[]{"Education Sector",     "education-sector",     "#D97706", "#FFFBEB"},
        new Object[]{"Indian Politics",      "indian-politics",      "#DC2626", "#FEF2F2"},
        new Object[]{"Global Politics",      "global-politics",      "#0E7490", "#ECFEFF"},
        new Object[]{"Entertainment",        "entertainment",        "#A855F7", "#F5F3FF"},
        new Object[]{"Fashion",              "fashion",              "#EC4899", "#FDF2F8"},
        new Object[]{"Sports",               "sports",               "#EA580C", "#FFF7ED"},
        new Object[]{"Environment",          "environment",          "#059669", "#ECFDF5"},
        new Object[]{"Economics",            "economics",            "#0284C7", "#E0F2FE"}
    );

    @Override
    public void run(ApplicationArguments args) {
        if (categoryRepository.count() == 0) {
            log.info("Seeding categories...");
            CATEGORIES.forEach(row -> {
                Category cat = new Category();
                cat.setName((String) row[0]);
                cat.setSlug((String) row[1]);
                cat.setAccentColor((String) row[2]);
                cat.setLightBgColor((String) row[3]);
                categoryRepository.save(cat);
            });
            log.info("Seeded {} categories", CATEGORIES.size());
        }
    }
}
