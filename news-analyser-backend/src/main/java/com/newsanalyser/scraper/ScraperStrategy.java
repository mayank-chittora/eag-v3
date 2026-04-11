package com.newsanalyser.scraper;

import com.newsanalyser.exception.ScraperException;

import java.util.List;

public interface ScraperStrategy {
    String getSourceName();
    String getSourceUrl();
    List<RawArticle> scrape() throws ScraperException;
}
