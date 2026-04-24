package com.newsanalyser.scraper.sources;

import com.newsanalyser.scraper.AbstractRssScraper;
import org.springframework.stereotype.Component;

@Component
public class JapanNewsScraper extends AbstractRssScraper {
    @Override public String getSourceName() { return "Japan News"; }
    @Override public String getSourceUrl()  { return "https://japannews.yomiuri.co.jp/"; }
    @Override protected String getRssFeedUrl() { return "https://japannews.yomiuri.co.jp/feed/"; }
}
