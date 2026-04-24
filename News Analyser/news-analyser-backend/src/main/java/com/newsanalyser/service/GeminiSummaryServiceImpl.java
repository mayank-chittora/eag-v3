package com.newsanalyser.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.newsanalyser.config.GeminiClient;
import com.newsanalyser.dto.request.SummaryRequest;
import com.newsanalyser.dto.response.NewsArticleDto;
import com.newsanalyser.dto.response.SseEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
@RequiredArgsConstructor
@Slf4j
public class GeminiSummaryServiceImpl implements GeminiSummaryService {

    private static final Logger LLM_LOG = LoggerFactory.getLogger("LLM_INTERACTIONS");

    private final NewsService newsService;
    private final GeminiClient geminiClient;
    private final ObjectMapper objectMapper;

    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

    @Override
    public SseEmitter generateSummary(SummaryRequest request) {
        SseEmitter emitter = new SseEmitter(300_000L);
        executor.submit(() -> runAgenticLoop(emitter, request));
        return emitter;
    }

    private void runAgenticLoop(SseEmitter emitter, SummaryRequest request) {
        try {
            // --- Tool 1: fetch_daily_news ---
            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.thinking)
                    .content("Fetching today's news for your selected categories...")
                    .build());

            LLM_LOG.debug("[TOOL CALL] fetch_daily_news | date={} | categories={}",
                    request.getDate(), request.getCategories());

            List<NewsArticleDto> articles = newsService.getNewsByDateAndCategories(
                    request.getDate(), request.getCategories());

            LLM_LOG.debug("[TOOL RESULT] fetch_daily_news | count={}", articles.size());

            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.tool_result)
                    .toolName("fetch_daily_news")
                    .content("Retrieved " + articles.size() + " articles across "
                            + request.getCategories().size() + " categories")
                    .articleCount(articles.size())
                    .build());

            if (articles.isEmpty()) {
                emit(emitter, SseEvent.builder()
                        .type(SseEvent.EventType.error)
                        .content("No articles found for the selected categories and date. "
                                + "Try a different date or broader category selection.")
                        .build());
                emitter.complete();
                return;
            }

            String articlesJson = buildArticlesJson(articles);
            List<String> industries = deriveIndustries(request.getCategories());

            // --- Tool 2: create_news_summary ---
            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.thinking)
                    .content("Generating a cohesive news summary...")
                    .build());
            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.tool_call)
                    .toolName("create_news_summary")
                    .content("Summarising " + articles.size() + " articles with Gemini 2.5 Flash")
                    .build());

            String summaryPrompt = buildSummaryPrompt(articlesJson, request.getDate());

            LLM_LOG.debug("[TOOL CALL] create_news_summary | date={} | article_count={}",
                    request.getDate(), articles.size());

            String summaryText = geminiClient.generateText(summaryPrompt, 0.3);

            LLM_LOG.debug("[TOOL RESULT] create_news_summary | response_length={} | preview={}",
                    summaryText.length(),
                    summaryText.substring(0, Math.min(500, summaryText.length())));

            streamText(emitter, summaryText);

            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.tool_result)
                    .toolName("create_news_summary")
                    .content("Summary generated")
                    .build());

            // --- Tool 3: analyze_market_impact ---
            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.thinking)
                    .content("Analysing stock market implications...")
                    .build());
            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.tool_call)
                    .toolName("analyze_market_impact")
                    .content("Evaluating impact on: " + String.join(", ", industries))
                    .build());

            String marketPrompt = buildMarketPrompt(articlesJson, industries, request.getDate());

            LLM_LOG.debug("[TOOL CALL] analyze_market_impact | date={} | industries={}",
                    request.getDate(), industries);

            String marketText = geminiClient.generateText(marketPrompt, 0.2);

            LLM_LOG.debug("[TOOL RESULT] analyze_market_impact | response_length={} | preview={}",
                    marketText.length(),
                    marketText.substring(0, Math.min(500, marketText.length())));

            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.tool_result)
                    .toolName("analyze_market_impact")
                    .content("Market impact analysis complete")
                    .build());

            streamText(emitter, marketText);

            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.done)
                    .content("Summary generation complete")
                    .build());
            emitter.complete();

        } catch (Exception e) {
            log.error("Gemini agentic loop failed", e);
            LLM_LOG.error("[ERROR] Agentic loop failed: {}", e.getMessage());
            try {
                emit(emitter, SseEvent.builder()
                        .type(SseEvent.EventType.error)
                        .content("Summary generation failed: " + e.getMessage())
                        .build());
                emitter.complete();
            } catch (IOException ignored) {}
        }
    }

    private String buildArticlesJson(List<NewsArticleDto> articles) throws Exception {
        var simplified = articles.stream().map(a -> Map.of(
                "headline", a.getHeadline() != null ? a.getHeadline() : "",
                "summary", a.getSummary() != null ? a.getSummary() : "",
                "source", a.getSourceName() != null ? a.getSourceName() : "",
                "sentiment", a.getSentiment() != null ? a.getSentiment().toString() : "NEUTRAL",
                "categories", a.getCategories().stream()
                        .map(c -> c.getName()).toList()
        )).toList();
        return objectMapper.writeValueAsString(simplified);
    }

    private String buildSummaryPrompt(String articlesJson, String date) {
        return """
                You are an expert news analyst. Below is a JSON array of news articles published on %s.

                Articles:
                %s

                Write a cohesive, well-structured markdown summary of today's most important news.

                Format your response as:
                ## Today's News Summary

                Write 3-5 paragraphs that weave together the key stories, highlight major themes, \
                and provide context. Use **bold** for key entities and developments. \
                Group related stories thematically. Write in a clear, professional tone \
                suitable for both students and investors.
                """.formatted(date, articlesJson);
    }

    private String buildMarketPrompt(String articlesJson, List<String> industries, String date) {
        return """
                You are a seasoned financial analyst specialising in Indian and global markets.
                Below are news articles from %s for the following sectors: %s.

                Articles:
                %s

                Provide a structured markdown analysis of how these developments may affect \
                the Indian stock market (BSE/NSE) and relevant global indices.

                Format your response as:
                ## Market Impact Analysis

                For each relevant sector provide:
                - **Sentiment**: Bullish / Bearish / Neutral
                - **Key driver**: The specific news driving the outlook
                - **Watch list**: Stock categories or sectors to monitor
                - **Risk factors**: Key risks to the outlook

                End with a brief **Overall Market Outlook** paragraph. \
                Be specific, cite headlines, and avoid generic statements.
                """.formatted(date, String.join(", ", industries), articlesJson);
    }

    private void streamText(SseEmitter emitter, String text) throws IOException, InterruptedException {
        String[] words = text.split("(?<=\\s)");
        StringBuilder buffer = new StringBuilder();
        for (String word : words) {
            buffer.append(word);
            if (buffer.length() >= 60 || word.matches(".*[.!?]\\s*")) {
                emit(emitter, SseEvent.builder()
                        .type(SseEvent.EventType.text_chunk)
                        .content(buffer.toString())
                        .build());
                buffer.setLength(0);
                Thread.sleep(20);
            }
        }
        if (!buffer.isEmpty()) {
            emit(emitter, SseEvent.builder()
                    .type(SseEvent.EventType.text_chunk)
                    .content(buffer.toString())
                    .build());
        }
    }

    private void emit(SseEmitter emitter, SseEvent event) throws IOException {
        String json = objectMapper.writeValueAsString(event);
        emitter.send(SseEmitter.event()
                .name(event.getType().name())
                .data(json));
    }

    private List<String> deriveIndustries(List<String> slugs) {
        Map<String, String> slugToIndustry = Map.of(
                "share-market", "Share Market & Equities",
                "it-sector", "Information Technology",
                "economics", "Macroeconomics & Monetary Policy",
                "manufacturing-sector", "Manufacturing & Industrial",
                "healthcare-sector", "Healthcare & Pharma",
                "agriculture-sector", "Agriculture & Agri-commodities"
        );
        List<String> result = slugs.stream()
                .map(s -> slugToIndustry.getOrDefault(s, s.replace("-", " ")))
                .distinct()
                .toList();
        return result.isEmpty() ? List.of("General Markets") : result;
    }
}
