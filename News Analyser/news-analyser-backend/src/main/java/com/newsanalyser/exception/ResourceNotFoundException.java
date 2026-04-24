package com.newsanalyser.exception;

public class ResourceNotFoundException extends NewsAnalyserException {
    public ResourceNotFoundException(String resource, Object id) {
        super(resource + " not found: " + id);
    }
}
