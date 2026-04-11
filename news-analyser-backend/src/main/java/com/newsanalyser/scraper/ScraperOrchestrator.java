package com.newsanalyser.scraper;

import com.newsanalyser.exception.ScraperException;
import com.newsanalyser.model.*;
import com.newsanalyser.repository.CategoryRepository;
import com.newsanalyser.repository.NewsArticleRepository;
import com.newsanalyser.sentiment.SentimentAnalyser;
import com.newsanalyser.util.AppConstants;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.CacheManager;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.*;

@Component
@RequiredArgsConstructor
@Slf4j
public class ScraperOrchestrator {

    private final List<ScraperStrategy> scrapers;
    private final NewsArticleRepository articleRepository;
    private final CategoryRepository categoryRepository;
    private final SentimentAnalyser sentimentAnalyser;
    private final CacheManager cacheManager;

    // Category keyword mapping for auto-assignment
    private static final Map<String, List<String>> CATEGORY_KEYWORDS = Map.ofEntries(
        Map.entry("share-market",         List.of("stock", "shares", "sensex", "nifty", "bse", "nse", "market", "equity", "trading", "investor")),
        Map.entry("agriculture-sector",   List.of("agriculture", "farm", "crop", "harvest", "fertilizer", "irrigation", "farmer", "kisan", "food grain")),
        Map.entry("manufacturing-sector", List.of("manufacturing", "factory", "production", "industry", "automobile", "steel", "cement")),
        Map.entry("it-sector",            List.of("technology", "software", "it sector", "ai", "artificial intelligence", "startup", "tech", "digital", "cybersecurity", "cloud")),
        Map.entry("healthcare-sector",    List.of("health", "hospital", "medicine", "pharma", "drug", "vaccine", "disease", "medical", "doctor", "patient")),
        Map.entry("hospitality-sector",   List.of("hotel", "tourism", "travel", "hospitality", "restaurant", "airline", "aviation")),
        Map.entry("education-sector",     List.of("education", "school", "university", "exam", "student", "college", "upsc", "curriculum")),
        Map.entry("indian-politics",      List.of("modi", "congress", "bjp", "parliament", "lok sabha", "rajya sabha", "election", "india government", "minister")),
        Map.entry("global-politics",      List.of("un", "united nations", "nato", "geopolitics", "diplomacy", "president", "prime minister", "war", "sanction", "treaty")),
        Map.entry("entertainment",        List.of("bollywood", "hollywood", "movie", "film", "celebrity", "actor", "music", "entertainment")),
        Map.entry("fashion",              List.of("fashion", "design", "clothes", "luxury", "brand", "style")),
        Map.entry("sports",               List.of("cricket", "football", "ipl", "fifa", "olympics", "sports", "tennis", "athlete", "championship")),
        Map.entry("environment",          List.of("climate", "environment", "pollution", "carbon", "renewable", "sustainability", "green energy", "deforestation")),
        Map.entry("economics",            List.of("gdp", "inflation", "economy", "rbi", "fiscal", "monetary", "budget", "trade", "export", "import", "recession"))
    );

    public int scrapeAll() {
        int totalNew = 0;
        List<Category> allCategories = categoryRepository.findAll();
        Map<String, Category> categoryBySlug = new HashMap<>();
        allCategories.forEach(c -> categoryBySlug.put(c.getSlug(), c));

        for (ScraperStrategy scraper : scrapers) {
            try {
                List<RawArticle> articles = scrapeWithRetry(scraper, 3);
                int saved = persistArticles(articles, categoryBySlug);
                totalNew += saved;
                log.info("[{}] Saved {} new articles", scraper.getSourceName(), saved);
            } catch (Exception e) {
                log.error("[{}] Scraping failed after retries: {}", scraper.getSourceName(), e.getMessage());
            }
        }

        evictNewsFeedCache();
        return totalNew;
    }

    private List<RawArticle> scrapeWithRetry(ScraperStrategy scraper, int maxRetries) throws ScraperException {
        int attempt = 0;
        long[] delays = {5_000, 30_000, 120_000};
        while (true) {
            try {
                return scraper.scrape();
            } catch (ScraperException e) {
                attempt++;
                if (attempt >= maxRetries) throw e;
                long delay = delays[Math.min(attempt - 1, delays.length - 1)];
                log.warn("[{}] Attempt {} failed, retrying in {}ms: {}", scraper.getSourceName(), attempt, delay, e.getMessage());
                try { Thread.sleep(delay); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); }
            }
        }
    }

    private int persistArticles(List<RawArticle> rawArticles, Map<String, Category> categoryBySlug) {
        int saved = 0;
        for (RawArticle raw : rawArticles) {
            try {
                if (articleRepository.existsByUrl(raw.getUrl())) continue;

                SentimentLabel sentiment = sentimentAnalyser.analyse(
                    raw.getHeadline() + " " + (raw.getSummary() != null ? raw.getSummary().substring(0, Math.min(150, raw.getSummary().length())) : "")
                );

                Set<Category> categories = assignCategories(raw, categoryBySlug);

                NewsArticle article = NewsArticle.builder()
                    .url(raw.getUrl())
                    .headline(raw.getHeadline())
                    .summary(raw.getSummary())
                    .sourceName(raw.getSourceName())
                    .imageUrl(raw.getImageUrl())
                    .publishedAt(raw.getPublishedAt())
                    .scrapedAt(LocalDateTime.now())
                    .sentiment(sentiment)
                    .categories(categories)
                    .build();

                articleRepository.save(article);
                saved++;
            } catch (Exception e) {
                log.warn("Failed to persist article {}: {}", raw.getUrl(), e.getMessage());
            }
        }
        return saved;
    }

    private Set<Category> assignCategories(RawArticle raw, Map<String, Category> categoryBySlug) {
        Set<Category> assigned = new HashSet<>();
        String text = (raw.getHeadline() + " " + raw.getSummary()).toLowerCase();

        for (Map.Entry<String, List<String>> entry : CATEGORY_KEYWORDS.entrySet()) {
            for (String keyword : entry.getValue()) {
                if (text.contains(keyword)) {
                    Category cat = categoryBySlug.get(entry.getKey());
                    if (cat != null) assigned.add(cat);
                    break;
                }
            }
        }

        // Also use RSS category hints
        if (raw.getCategoryHints() != null) {
            for (String hint : raw.getCategoryHints()) {
                categoryBySlug.values().stream()
                    .filter(c -> c.getName().toLowerCase().contains(hint) || hint.contains(c.getSlug()))
                    .findFirst()
                    .ifPresent(assigned::add);
            }
        }

        // Default: assign "Global Politics" or "Economics" if nothing matched
        if (assigned.isEmpty()) {
            Category fallback = categoryBySlug.get("global-politics");
            if (fallback != null) assigned.add(fallback);
        }

        return assigned;
    }

    private void evictNewsFeedCache() {
        try {
            var cache = cacheManager.getCache(AppConstants.CACHE_NEWS_FEED);
            if (cache != null) cache.clear();
        } catch (Exception e) {
            log.warn("Failed to evict news feed cache: {}", e.getMessage());
        }
    }
}
