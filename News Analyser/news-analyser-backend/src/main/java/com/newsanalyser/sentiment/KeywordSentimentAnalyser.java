package com.newsanalyser.sentiment;

import com.newsanalyser.model.SentimentLabel;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Locale;

/**
 * Keyword-based sentiment analyser.
 * Classifies text as POSITIVE, NEGATIVE, or NEUTRAL based on weighted keyword matching.
 * This is a lightweight implementation suitable for news headline analysis.
 */
@Service
@Slf4j
public class KeywordSentimentAnalyser implements SentimentAnalyser {

    private static final List<String> POSITIVE_WORDS = List.of(
        "growth", "increase", "rise", "improve", "gain", "profit", "success", "record",
        "breakthrough", "advance", "recover", "boost", "surge", "rally", "expand", "win",
        "achieve", "positive", "strong", "benefit", "progress", "development", "invest",
        "innovation", "launch", "award", "peace", "cooperation", "agreement", "deal",
        "approval", "celebrate", "upgrade", "milestone", "opportunity", "promising"
    );

    private static final List<String> NEGATIVE_WORDS = List.of(
        "fall", "decline", "drop", "crash", "loss", "fail", "crisis", "threat", "war",
        "attack", "violence", "death", "dead", "kill", "bomb", "terror", "disaster",
        "collapse", "scandal", "corruption", "fraud", "protest", "strike", "riot",
        "inflation", "recession", "bankrupt", "unemployment", "poverty", "drought",
        "flood", "earthquake", "explosion", "shooting", "arrest", "charge", "sanction",
        "ban", "blocked", "delayed", "cut", "reduce", "warning", "concern", "risk",
        "dangerous", "injured", "hurt", "devastate", "tragedy", "controversy"
    );

    @Override
    public SentimentLabel analyse(String text) {
        if (text == null || text.isBlank()) return SentimentLabel.NEUTRAL;

        String lower = text.toLowerCase(Locale.ENGLISH);
        int positiveScore = 0;
        int negativeScore = 0;

        for (String word : POSITIVE_WORDS) {
            if (lower.contains(word)) positiveScore++;
        }
        for (String word : NEGATIVE_WORDS) {
            if (lower.contains(word)) negativeScore++;
        }

        log.debug("Sentiment scores — positive:{} negative:{} for: {}",
            positiveScore, negativeScore, text.substring(0, Math.min(80, text.length())));

        if (positiveScore > negativeScore && positiveScore >= 2) return SentimentLabel.POSITIVE;
        if (negativeScore > positiveScore && negativeScore >= 2) return SentimentLabel.NEGATIVE;
        if (positiveScore > 0 && negativeScore == 0) return SentimentLabel.POSITIVE;
        if (negativeScore > 0 && positiveScore == 0) return SentimentLabel.NEGATIVE;
        return SentimentLabel.NEUTRAL;
    }
}
