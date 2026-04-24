package com.newsanalyser.sentiment;

import com.newsanalyser.model.SentimentLabel;

public interface SentimentAnalyser {
    SentimentLabel analyse(String text);
}
