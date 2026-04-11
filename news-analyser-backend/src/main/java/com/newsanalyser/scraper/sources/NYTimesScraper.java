package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class NYTimesScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "New York Times"; }
    @Override public String getSourceUrl()  { return "https://www.nytimes.com/"; }
    @Override protected String getRssFeedUrl() { return "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"; }
}
