package com.newsanalyser.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class SseEvent {

    public enum EventType {
        thinking,
        tool_call,
        tool_result,
        text_chunk,
        done,
        error
    }

    private EventType type;
    private String content;
    private String toolName;
    private Integer articleCount;
}
