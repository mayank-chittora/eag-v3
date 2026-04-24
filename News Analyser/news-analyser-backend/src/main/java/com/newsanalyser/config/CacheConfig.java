package com.newsanalyser.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import com.newsanalyser.util.AppConstants;
import org.springframework.cache.CacheManager;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

import java.util.concurrent.TimeUnit;

@Configuration
@Profile("dev")
public class CacheConfig {

    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager manager = new CaffeineCacheManager(
            AppConstants.CACHE_NEWS_FEED,
            AppConstants.CACHE_CATEGORIES,
            AppConstants.CACHE_SOURCES,
            AppConstants.CACHE_DIGESTS
        );
        manager.setCaffeine(Caffeine.newBuilder()
                .maximumSize(500)
                .expireAfterWrite(30, TimeUnit.MINUTES)
                .recordStats());
        return manager;
    }
}
