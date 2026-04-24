package com.newsanalyser.exception;

public class NewsAnalyserException extends RuntimeException {
    public NewsAnalyserException(String message) {
        super(message);
    }
    public NewsAnalyserException(String message, Throwable cause) {
        super(message, cause);
    }
}
