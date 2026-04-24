CREATE TABLE news_articles (
    id           BIGSERIAL PRIMARY KEY,
    url          VARCHAR(1000) NOT NULL UNIQUE,
    headline     VARCHAR(500) NOT NULL,
    summary      TEXT,
    source_name  VARCHAR(200) NOT NULL,
    image_url    VARCHAR(500),
    published_at TIMESTAMP NOT NULL,
    scraped_at   TIMESTAMP NOT NULL,
    sentiment    VARCHAR(20) NOT NULL
);

CREATE INDEX idx_articles_published_at ON news_articles (published_at DESC);
CREATE INDEX idx_articles_sentiment    ON news_articles (sentiment);
CREATE INDEX idx_articles_source       ON news_articles (source_name);
CREATE INDEX idx_articles_scraped_at   ON news_articles (scraped_at DESC);

CREATE TABLE article_categories (
    article_id  BIGINT NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES categories(id),
    PRIMARY KEY (article_id, category_id)
);

CREATE INDEX idx_article_categories_category ON article_categories (category_id);
