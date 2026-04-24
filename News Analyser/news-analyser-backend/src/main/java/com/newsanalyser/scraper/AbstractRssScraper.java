package com.newsanalyser.scraper;

import com.newsanalyser.exception.ScraperException;
import com.rometools.rome.feed.synd.SyndEntry;
import com.rometools.rome.feed.synd.SyndFeed;
import com.rometools.rome.io.SyndFeedInput;
import com.rometools.rome.io.XmlReader;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.util.StringUtils;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@Slf4j
public abstract class AbstractRssScraper implements ScraperStrategy {

    @Value("${app.scraper.user-agent:NewsAnalyser/1.0 (educational project)}")
    protected String userAgent;

    @Value("${app.scraper.connection-timeout-ms:10000}")
    protected int connectionTimeout;

    @Value("${app.scraper.read-timeout-ms:30000}")
    protected int readTimeout;

    protected abstract String getRssFeedUrl();

    @Override
    public List<RawArticle> scrape() throws ScraperException {
        String feedUrl = getRssFeedUrl();
        log.info("Scraping RSS feed: {} from {}", getSourceName(), feedUrl);
        try {
            HttpURLConnection conn = (HttpURLConnection) new URL(feedUrl).openConnection();
            conn.setConnectTimeout(connectionTimeout);
            conn.setReadTimeout(readTimeout);
            conn.setRequestProperty("User-Agent", userAgent);
            conn.setRequestProperty("Accept", "application/rss+xml, application/xml, text/xml, */*");

            try (InputStream is = conn.getInputStream();
                 XmlReader reader = new XmlReader(is)) {
                SyndFeed feed = new SyndFeedInput().build(reader);
                return parseFeedEntries(feed.getEntries());
            }
        } catch (Exception e) {
            throw new ScraperException(getSourceName(), "Failed to fetch RSS: " + feedUrl, e);
        }
    }

    protected List<RawArticle> parseFeedEntries(List<SyndEntry> entries) {
        List<RawArticle> articles = new ArrayList<>();
        for (SyndEntry entry : entries) {
            try {
                String url = entry.getLink();
                if (!StringUtils.hasText(url)) continue;

                String headline = entry.getTitle() != null ? entry.getTitle().trim() : "";
                if (!StringUtils.hasText(headline)) continue;

                String summary = extractDescription(entry);
                LocalDateTime publishedAt = toLocalDateTime(entry.getPublishedDate());
                String imageUrl = extractImageUrl(entry);

                articles.add(RawArticle.builder()
                        .url(url)
                        .headline(headline)
                        .summary(summary)
                        .sourceName(getSourceName())
                        .imageUrl(imageUrl)
                        .publishedAt(publishedAt != null ? publishedAt : LocalDateTime.now())
                        .categoryHints(extractCategoryHints(entry))
                        .build());
            } catch (Exception e) {
                log.warn("[{}] Failed to parse entry: {}", getSourceName(), e.getMessage());
            }
        }
        log.info("[{}] Parsed {} articles", getSourceName(), articles.size());
        return articles;
    }

    protected String extractDescription(SyndEntry entry) {
        if (entry.getDescription() != null && StringUtils.hasText(entry.getDescription().getValue())) {
            // Strip HTML tags from description
            return entry.getDescription().getValue()
                    .replaceAll("<[^>]+>", " ")
                    .replaceAll("\\s+", " ")
                    .trim();
        }
        return "";
    }

    protected String extractImageUrl(SyndEntry entry) {
        // Try to extract image from enclosures
        if (entry.getEnclosures() != null && !entry.getEnclosures().isEmpty()) {
            String encUrl = entry.getEnclosures().get(0).getUrl();
            if (StringUtils.hasText(encUrl)) return encUrl;
        }
        // Try to extract from media:content
        if (entry.getForeignMarkup() != null) {
            for (var el : entry.getForeignMarkup()) {
                if ("content".equals(el.getName()) || "thumbnail".equals(el.getName())) {
                    String url = el.getAttributeValue("url");
                    if (StringUtils.hasText(url)) return url;
                }
            }
        }
        return null;
    }

    protected List<String> extractCategoryHints(SyndEntry entry) {
        List<String> hints = new ArrayList<>();
        if (entry.getCategories() != null) {
            entry.getCategories().forEach(cat -> {
                if (cat.getName() != null) hints.add(cat.getName().toLowerCase());
            });
        }
        return hints;
    }

    protected LocalDateTime toLocalDateTime(Date date) {
        if (date == null) return null;
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
