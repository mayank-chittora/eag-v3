package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class PeoplesDailyScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "People's Daily"; }
    @Override public String getSourceUrl()  { return "https://en.people.cn/"; }
    @Override protected String getRssFeedUrl() { return "http://en.people.cn/rss/90777.xml"; }
}
