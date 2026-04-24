package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class TheHinduScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "The Hindu"; }
    @Override public String getSourceUrl()  { return "https://www.thehindu.com/"; }
    @Override protected String getRssFeedUrl() { return "https://www.thehindu.com/feeder/default.rss"; }
}
