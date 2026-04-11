package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class WallStreetJournalScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Wall Street Journal"; }
    @Override public String getSourceUrl()  { return "https://www.wsj.com/"; }
    @Override protected String getRssFeedUrl() { return "https://feeds.a.dj.com/rss/RSSWorldNews.xml"; }
}
