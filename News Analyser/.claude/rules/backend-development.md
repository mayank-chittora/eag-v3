# News Analyser — Backend Development Rules

## 1. Project Structure

```
news-analyser-backend/
├── src/
│   ├── main/
│   │   ├── java/com/newsanalyser/
│   │   │   ├── NewsAnalyserApplication.java       # Spring Boot main class
│   │   │   ├── config/
│   │   │   │   ├── WebConfig.java                 # CORS configuration
│   │   │   │   ├── CacheConfig.java               # Caffeine / Redis config
│   │   │   │   ├── SecurityConfig.java            # Spring Security + rate limiting
│   │   │   │   └── SchedulerConfig.java           # @EnableScheduling
│   │   │   ├── controller/
│   │   │   │   ├── NewsController.java
│   │   │   │   ├── CategoryController.java
│   │   │   │   ├── HistoricalController.java
│   │   │   │   ├── QuizController.java
│   │   │   │   └── HealthController.java
│   │   │   ├── service/
│   │   │   │   ├── NewsAggregatorService.java     # Orchestrates scraping + storage
│   │   │   │   ├── NewsAggregatorServiceImpl.java
│   │   │   │   ├── SentimentService.java
│   │   │   │   ├── SentimentServiceImpl.java
│   │   │   │   ├── QuizGeneratorService.java
│   │   │   │   ├── QuizGeneratorServiceImpl.java
│   │   │   │   ├── HistoricalDataService.java
│   │   │   │   └── HistoricalDataServiceImpl.java
│   │   │   ├── repository/
│   │   │   │   ├── NewsArticleRepository.java
│   │   │   │   ├── CategoryRepository.java
│   │   │   │   ├── QuizQuestionRepository.java
│   │   │   │   └── HistoricalSnapshotRepository.java
│   │   │   ├── model/
│   │   │   │   ├── NewsArticle.java
│   │   │   │   ├── Category.java
│   │   │   │   ├── SentimentLabel.java            # Enum: POSITIVE, NEGATIVE, NEUTRAL
│   │   │   │   ├── QuizQuestion.java
│   │   │   │   └── HistoricalSnapshot.java
│   │   │   ├── dto/
│   │   │   │   ├── request/
│   │   │   │   │   ├── NewsFilterRequest.java
│   │   │   │   │   ├── HistoricalRequest.java
│   │   │   │   │   └── QuizSubmitRequest.java
│   │   │   │   └── response/
│   │   │   │       ├── NewsArticleDto.java
│   │   │   │       ├── CategoryDto.java
│   │   │   │       ├── QuizQuestionDto.java
│   │   │   │       ├── QuizResultDto.java
│   │   │   │       └── ApiResponse.java           # Generic wrapper
│   │   │   ├── scraper/
│   │   │   │   ├── ScraperStrategy.java           # Interface
│   │   │   │   ├── ScraperRegistry.java           # Holds all scrapers
│   │   │   │   ├── ScraperOrchestrator.java       # Runs all registered scrapers
│   │   │   │   └── sources/
│   │   │   │       ├── TimesOfIndiaScraper.java
│   │   │   │       ├── TheHinduScraper.java
│   │   │   │       ├── HindustanTimesScraper.java
│   │   │   │       ├── BBCScraper.java
│   │   │   │       ├── NYTimesScraper.java
│   │   │   │       ├── WallStreetJournalScraper.java
│   │   │   │       ├── TheGuardianScraper.java
│   │   │   │       ├── TelegraphScraper.java
│   │   │   │       ├── JapanNewsScraper.java
│   │   │   │       ├── FoxNewsScraper.java
│   │   │   │       ├── StraitTimesScraper.java
│   │   │   │       ├── AlJazeeraScraper.java
│   │   │   │       └── PeoplesDailyScraper.java
│   │   │   ├── sentiment/
│   │   │   │   ├── SentimentAnalyser.java         # Interface
│   │   │   │   └── CoreNLPSentimentAnalyser.java  # Stanford CoreNLP implementation
│   │   │   ├── scheduler/
│   │   │   │   ├── ScraperScheduler.java          # @Scheduled scraping jobs
│   │   │   │   └── HistoricalSnapshotScheduler.java
│   │   │   ├── exception/
│   │   │   │   ├── GlobalExceptionHandler.java    # @RestControllerAdvice
│   │   │   │   ├── ScraperException.java
│   │   │   │   ├── SentimentException.java
│   │   │   │   └── ResourceNotFoundException.java
│   │   │   └── util/
│   │   │       └── AppConstants.java
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       └── db/migration/                      # Flyway SQL migrations
│   │           ├── V1__create_categories.sql
│   │           ├── V2__create_news_articles.sql
│   │           ├── V3__create_quiz_questions.sql
│   │           └── V4__create_historical_snapshots.sql
│   └── test/
│       └── java/com/newsanalyser/
│           ├── controller/                        # @WebMvcTest slices
│           ├── service/                           # @ExtendWith(MockitoExtension.class)
│           └── scraper/                           # @SpringBootTest scraper tests
├── pom.xml
└── .env.example
```

---

## 2. Tech Stack (Exact Versions)

| Dependency              | Version   | Purpose                              |
|-------------------------|-----------|--------------------------------------|
| Java                    | 21 (LTS)  | Language                             |
| Spring Boot             | 3.2.x     | Framework                            |
| Maven                   | 3.9.x     | Build tool                           |
| Spring Data JPA         | (bundled) | ORM                                  |
| Hibernate               | 6.x       | JPA implementation                   |
| PostgreSQL Driver       | 42.x      | JDBC driver                          |
| Flyway                  | 9.x       | DB migrations                        |
| HikariCP                | (bundled) | Connection pooling                   |
| Jsoup                   | 1.17.x    | HTML scraping                        |
| Rome                    | 2.1.x     | RSS/Atom feed parsing                |
| Stanford CoreNLP        | 4.5.x     | Sentiment analysis NLP               |
| Caffeine                | 3.x       | In-process cache (dev)               |
| Spring Data Redis       | (bundled) | Cache (prod)                         |
| Lettuce                 | (bundled) | Redis client                         |
| Spring Security         | 6.x       | Security configuration               |
| Bucket4j                | 8.x       | Rate limiting                        |
| SpringDoc OpenAPI       | 2.x       | Swagger UI / API docs                |
| Lombok                  | latest    | Boilerplate reduction                |
| MapStruct               | 1.5.x     | Entity ↔ DTO mapping                 |
| Guava                   | 32.x      | Utilities                            |
| JUnit 5                 | (bundled) | Testing                              |
| Mockito                 | (bundled) | Mocking                              |
| Testcontainers          | 1.19.x    | Integration tests with real DB       |

---

## 3. REST API Contract

### 3.1 URL Conventions
- Base path: `/api/v1/`
- Resource names: plural, lowercase, hyphenated (e.g., `/news-articles`, not `/newsArticles`)
- No verbs in URLs. Use HTTP methods for semantics.
- Versioning: path-based (`/api/v1/`). When breaking changes are needed, add `/api/v2/`.

### 3.2 Endpoint Definitions

#### News
| Method | Path                          | Description                                      |
|--------|-------------------------------|--------------------------------------------------|
| GET    | `/api/v1/news`                | Paginated news feed with filters                 |
| GET    | `/api/v1/news/{id}`           | Single article by ID                             |

Query params for `/api/v1/news`:
- `categories` (comma-separated list): e.g., `IT+Sector,Sports`
- `sentiment` (optional): `POSITIVE`, `NEGATIVE`, `NEUTRAL`
- `sources` (optional, comma-separated)
- `page` (default: 0), `pageSize` (default: 20, max: 50)

#### Categories
| Method | Path                          | Description                                      |
|--------|-------------------------------|--------------------------------------------------|
| GET    | `/api/v1/categories`          | All available interest categories                |

#### Historical
| Method | Path                          | Description                                      |
|--------|-------------------------------|--------------------------------------------------|
| GET    | `/api/v1/historical`          | News for a specific past date                    |

Query params for `/api/v1/historical`:
- `date` (required): ISO-8601 format `YYYY-MM-DD`; max 1 year ago
- `categories`, `sentiment`, `page`, `pageSize` — same as news feed

#### Quiz
| Method | Path                          | Description                                      |
|--------|-------------------------------|--------------------------------------------------|
| GET    | `/api/v1/quiz/questions`      | Generate 10 MCQ questions from last 30 days      |
| POST   | `/api/v1/quiz/submit`         | Submit answers, receive scored result            |

#### Health
| Method | Path                          | Description                                      |
|--------|-------------------------------|--------------------------------------------------|
| GET    | `/api/v1/health`              | Service health check (uptime, DB, cache status) |

### 3.3 Standard Response Envelope
All responses (success and error) use this wrapper. Never return raw entities.

```java
// dto/response/ApiResponse.java
@Data
@Builder
public class ApiResponse<T> {
    private T data;
    private PageMeta meta;      // null for non-paginated responses
    private ApiError error;     // null on success

    @Data
    @Builder
    public static class PageMeta {
        private int page;
        private int pageSize;
        private long total;
        private int totalPages;
    }

    @Data
    @Builder
    public static class ApiError {
        private String code;
        private String message;
    }
}
```

### 3.4 HTTP Status Codes
| Scenario                    | Status Code |
|-----------------------------|-------------|
| Success with body           | 200         |
| Validation error            | 400         |
| Not found                   | 404         |
| Rate limit exceeded         | 429         |
| Internal server error       | 500         |
| Scraper/external source down| 503         |

---

## 4. Scraper Architecture

### 4.1 ScraperStrategy Interface
```java
public interface ScraperStrategy {
    String getSourceName();
    String getSourceUrl();
    List<RawArticle> scrape() throws ScraperException;
}
```

Every scraper implements this interface. `RawArticle` is an internal DTO (not persisted directly).

### 4.2 Scraping Rules
1. **Always check robots.txt before implementing a scraper.** If a path is disallowed, use the
   source's RSS feed instead. If no RSS and scraping is disallowed, omit that source.
2. **Prefer RSS parsing** (Rome library) over HTML scraping. RSS is more stable and intentional.
3. **Rate limit**: Maximum 1 request per source per 30 minutes. Use Caffeine to track last-scraped timestamps.
4. **Retry**: Use exponential backoff — 3 retries with delays of 5s, 30s, 2min. After 3 failures,
   log at ERROR level and skip (do not throw — other sources must still complete).
5. **Timeout**: HTTP connection timeout 10s, read timeout 30s.
6. **User-Agent header**: Set a descriptive user agent — `NewsAnalyser/1.0 (educational project)`.
7. **Deduplication**: Before persisting, check if `url` already exists in `news_articles` table.

### 4.3 ScraperRegistry
```java
@Component
public class ScraperRegistry {
    private final Map<String, ScraperStrategy> scrapers = new LinkedHashMap<>();

    @PostConstruct
    public void registerAll() {
        // Each scraper bean registers itself; or inject List<ScraperStrategy> via Spring
    }

    public List<ScraperStrategy> getAll() {
        return List.copyOf(scrapers.values());
    }
}
```

---

## 5. Sentiment Analysis Pipeline

### 5.1 Implementation
Use **Stanford CoreNLP** (edu.stanford.nlp) with the `sentiment` annotator.

```java
@Service
public class CoreNLPSentimentAnalyser implements SentimentAnalyser {
    // Initialise pipeline once at startup — CoreNLP is heavy
    private final StanfordCoreNLP pipeline;

    public CoreNLPSentimentAnalyser() {
        Properties props = new Properties();
        props.setProperty("annotators", "tokenize,ssplit,pos,parse,sentiment");
        this.pipeline = new StanfordCoreNLP(props);
    }

    @Override
    public SentimentLabel analyse(String text) {
        // Run on headline + first 2 sentences of summary
        // Aggregate sentence-level sentiment scores
        // Map: Very Positive/Positive → POSITIVE
        //       Negative/Very Negative → NEGATIVE
        //       Neutral                → NEUTRAL
    }
}
```

### 5.2 Rules
- Run sentiment analysis **after** scraping, before persistence.
- Analyse the article headline + first 150 characters of summary only (for performance).
- Confidence threshold: if > 60% of sentences are Neutral, label as NEUTRAL.
- Sentiment is stored with the article and never re-computed (unless re-scraping).
- If CoreNLP throws an exception, default to `SentimentLabel.NEUTRAL` and log a WARNING.

---

## 6. Data Models

### 6.1 NewsArticle
```java
@Entity
@Table(name = "news_articles",
       uniqueConstraints = @UniqueConstraint(columnNames = "url"))
public class NewsArticle {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 500)
    private String url;

    @Column(nullable = false, length = 300)
    private String headline;

    @Column(length = 1000)
    private String summary;

    @Column(nullable = false)
    private String sourceName;

    @Column(nullable = false)
    private LocalDateTime publishedAt;

    @Column(nullable = false)
    private LocalDateTime scrapedAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SentimentLabel sentiment;

    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(name = "article_categories")
    private Set<Category> categories;
}
```

### 6.2 Category
```java
@Entity
@Table(name = "categories")
public class Category {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String name;   // "Share Market", "IT Sector", etc.

    @Column(nullable = false)
    private String slug;   // "share-market", "it-sector"
}
```

### 6.3 QuizQuestion
```java
@Entity
@Table(name = "quiz_questions")
public class QuizQuestion {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 500)
    private String questionText;

    @ElementCollection
    @CollectionTable(name = "quiz_options")
    @Column(nullable = false)
    private List<String> options;   // Always 4 options

    @Column(nullable = false)
    private int correctOptionIndex; // 0-based index

    @ManyToOne
    private NewsArticle sourceArticle;

    @Column(nullable = false)
    private LocalDate generatedForDate;  // The date this question was relevant for
}
```

---

## 7. Caching Strategy

| Cache Name          | Implementation | TTL       | Eviction Trigger               |
|---------------------|----------------|-----------|--------------------------------|
| `news-feed`         | Caffeine/Redis | 30 min    | On new scrape completion       |
| `historical-{date}` | Caffeine/Redis | 24 hours  | Never (immutable historical)   |
| `categories`        | Caffeine/Redis | 1 hour    | Manual on category update      |
| `quiz-questions`    | None           | —         | Always fresh (do not cache)    |

Use Spring's `@Cacheable`, `@CacheEvict` annotations. Cache config in `CacheConfig.java`.

```yaml
# application-dev.yml — Caffeine
spring:
  cache:
    type: caffeine
  caffeine:
    spec: maximumSize=500,expireAfterWrite=30m

# application-prod.yml — Redis
spring:
  cache:
    type: redis
  data:
    redis:
      host: ${REDIS_HOST}
      port: ${REDIS_PORT}
```

---

## 8. Scheduling

```java
@Component
public class ScraperScheduler {
    // Scrape all sources every 30 minutes
    @Scheduled(fixedDelay = 30 * 60 * 1000, initialDelay = 60_000)
    public void scrapeAllSources() { ... }
}

@Component
public class HistoricalSnapshotScheduler {
    // Create daily snapshot at 00:05 AM
    @Scheduled(cron = "0 5 0 * * *")
    public void createDailySnapshot() { ... }
}
```

---

## 9. Error Handling

### 9.1 GlobalExceptionHandler
```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiResponse<Void>> handleNotFound(ResourceNotFoundException ex) {
        return ResponseEntity.status(404).body(
            ApiResponse.<Void>builder()
                .error(ApiResponse.ApiError.builder()
                    .code("NOT_FOUND").message(ex.getMessage()).build())
                .build()
        );
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(...) { ... }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGeneral(Exception ex) { ... }
}
```

### 9.2 Logging Standards
- Use SLF4J (`private static final Logger log = LoggerFactory.getLogger(MyClass.class)`)
- Never use `System.out.println`
- Log levels:
  - `DEBUG`: method entry/exit in controllers, cache hit/miss
  - `INFO`: scrape job start/complete, article count persisted
  - `WARN`: scraper retry, CoreNLP fallback to NEUTRAL
  - `ERROR`: scraper failed after all retries, DB write failure

---

## 10. Security

### 10.1 CORS
```java
// config/WebConfig.java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins(
                "http://localhost:5173",          // Vite dev server
                "${APP_FRONTEND_ORIGIN}"          // Production frontend URL
            )
            .allowedMethods("GET", "POST")
            .allowedHeaders("Content-Type", "Authorization")
            .maxAge(3600);
    }
}
```

### 10.2 Rate Limiting (Bucket4j)
- Default: 60 requests per minute per IP for all `/api/v1/` endpoints.
- Quiz endpoint: 10 quiz generations per IP per hour.
- Return `429 Too Many Requests` with `Retry-After` header when limit exceeded.

### 10.3 Credentials
- **Never** hardcode database passwords, Redis passwords, or API keys in source files.
- All secrets go in `application-prod.yml` via environment variable placeholders: `${DB_PASSWORD}`.
- `.env` files must be in `.gitignore`.

---

## 11. Controller Rules

1. Annotate with `@RestController @RequestMapping("/api/v1/{resource}")`.
2. Use `@Valid` on all `@RequestBody` and `@ModelAttribute` parameters.
3. Return `ResponseEntity<ApiResponse<T>>` on all endpoints.
4. Controllers must contain **NO business logic** — delegate everything to the service layer.
5. Log method entry at `DEBUG` level with sanitised parameters.
6. Use constructor injection — never `@Autowired` on fields.

---

## 12. Service Layer Rules

1. Define a service **interface** first, then the `@Service`-annotated implementation.
2. Use constructor injection exclusively.
3. Methods calling external systems (scrapers, CoreNLP, Redis) must declare or handle exceptions.
4. Services are the only layer that may call repositories directly.
5. Never call one service from another service if it creates a circular dependency — use events.
