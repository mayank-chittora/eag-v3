package com.newsanalyser.util;

import java.util.List;

public final class AppConstants {

    private AppConstants() {}

    public static final List<String> SUPPORTED_SOURCES = List.of(
        "Times of India",
        "The Hindu",
        "Hindustan Times",
        "BBC",
        "New York Times",
        "Wall Street Journal",
        "The Guardian",
        "Telegraph",
        "Japan News",
        "Fox News",
        "Straits Times",
        "Al Jazeera",
        "People's Daily"
    );

    public static final List<String> DEFAULT_CATEGORIES = List.of(
        "Share Market",
        "Agriculture Sector",
        "Manufacturing Sector",
        "IT Sector",
        "Healthcare Sector",
        "Hospitality Sector",
        "Education Sector",
        "Indian Politics",
        "Global Politics",
        "Entertainment",
        "Fashion",
        "Sports",
        "Environment",
        "Economics"
    );

    public static final String CACHE_NEWS_FEED = "news-feed";
    public static final String CACHE_CATEGORIES = "categories";
    public static final String CACHE_SOURCES = "sources";
    public static final String CACHE_DIGESTS = "digests";
}
