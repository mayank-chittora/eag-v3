package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class HindustanTimesScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Hindustan Times"; }
    @Override public String getSourceUrl()  { return "https://www.hindustantimes.com/"; }
    @Override protected String getRssFeedUrl() { return "https://www.hindustantimes.com/rss/topnews/rssfeed.xml"; }
}
