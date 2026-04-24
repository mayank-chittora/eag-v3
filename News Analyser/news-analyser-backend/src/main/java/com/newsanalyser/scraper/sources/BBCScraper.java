package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class BBCScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "BBC"; }
    @Override public String getSourceUrl()  { return "https://www.bbc.com/"; }
    @Override protected String getRssFeedUrl() { return "https://feeds.bbci.co.uk/news/world/rss.xml"; }
}
