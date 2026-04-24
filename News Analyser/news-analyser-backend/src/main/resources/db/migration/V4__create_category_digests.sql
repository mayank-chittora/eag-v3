CREATE TABLE category_digests (
    id             BIGSERIAL    PRIMARY KEY,
    date           DATE         NOT NULL,
    category_slug  VARCHAR(100) NOT NULL,
    sentiment      VARCHAR(20)  NOT NULL,
    digest_text    TEXT         NOT NULL,
    generated_at   TIMESTAMP    NOT NULL,
    CONSTRAINT uq_digest UNIQUE (date, category_slug, sentiment)
);

CREATE INDEX idx_digests_date ON category_digests(date);
