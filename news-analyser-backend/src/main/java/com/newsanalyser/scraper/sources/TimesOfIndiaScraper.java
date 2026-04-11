package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class TimesOfIndiaScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Times of India"; }
    @Override public String getSourceUrl()  { return "https://timesofindia.indiatimes.com/"; }
    @Override protected String getRssFeedUrl() { return "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"; }
}
