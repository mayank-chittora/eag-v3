package com.newsanalyser.scheduler;

import com.newsanalyser.scraper.ScraperOrchestrator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class ScraperScheduler {

    private final ScraperOrchestrator orchestrator;

    /**
     * Scrape all sources every 30 minutes.
     * Initial delay of 60s to allow app context to fully start.
     */
    @Scheduled(fixedDelayString = "${app.scraper.schedule-interval-ms:1800000}",
               initialDelay = 60_000)
    public void scrapeAllSources() {
        log.info("Scheduled scrape starting...");
        try {
            int count = orchestrator.scrapeAll();
            log.info("Scheduled scrape complete. {} new articles saved.", count);
        } catch (Exception e) {
            log.error("Scheduled scrape failed", e);
        }
    }
}
