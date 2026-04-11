package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class TelegraphScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Telegraph"; }
    @Override public String getSourceUrl()  { return "https://www.telegraph.co.uk/"; }
    @Override protected String getRssFeedUrl() { return "https://www.telegraph.co.uk/rss.xml"; }
}
