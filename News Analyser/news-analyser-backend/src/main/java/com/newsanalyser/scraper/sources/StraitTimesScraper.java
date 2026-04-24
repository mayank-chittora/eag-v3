package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class StraitTimesScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Straits Times"; }
    @Override public String getSourceUrl()  { return "https://www.straitstimes.com/global"; }
    @Override protected String getRssFeedUrl() { return "https://www.straitstimes.com/news/world/rss.xml"; }
}
