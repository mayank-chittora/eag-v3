package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class TheGuardianScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "The Guardian"; }
    @Override public String getSourceUrl()  { return "https://www.theguardian.com/international"; }
    @Override protected String getRssFeedUrl() { return "https://www.theguardian.com/world/rss"; }
}
