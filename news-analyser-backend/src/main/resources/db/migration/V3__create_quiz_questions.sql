CREATE TABLE quiz_questions (
    id                  BIGSERIAL PRIMARY KEY,
    question_text       VARCHAR(600) NOT NULL,
    correct_option_index INT NOT NULL,
    source_article_id   BIGINT REFERENCES news_articles(id) ON DELETE SET NULL,
    generated_for_date  DATE NOT NULL
);

CREATE INDEX idx_quiz_generated_date ON quiz_questions (generated_for_date);

CREATE TABLE quiz_options (
    question_id  BIGINT NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
    option_index INT NOT NULL,
    value        VARCHAR(300) NOT NULL,
    PRIMARY KEY (question_id, option_index)
);
