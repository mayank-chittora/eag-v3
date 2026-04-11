package com.newsanalyser.exception;

public class ScraperException extends NewsAnalyserException {
    public ScraperException(String source, String message) {
        super("[" + source + "] " + message);
    }
    public ScraperException(String source, String message, Throwable cause) {
        super("[" + source + "] " + message, cause);
    }
}
