package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class FoxNewsScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Fox News"; }
    @Override public String getSourceUrl()  { return "https://www.foxnews.com/"; }
    @Override protected String getRssFeedUrl() { return "https://moxie.foxnews.com/google-publisher/world.xml"; }
}
