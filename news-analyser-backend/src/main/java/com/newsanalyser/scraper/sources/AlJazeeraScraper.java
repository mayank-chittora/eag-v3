package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class AlJazeeraScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Al Jazeera"; }
    @Override public String getSourceUrl()  { return "https://www.aljazeera.com/"; }
    @Override protected String getRssFeedUrl() { return "https://www.aljazeera.com/xml/rss/all.xml"; }
}
