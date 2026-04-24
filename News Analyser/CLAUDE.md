# News Analyser — Project Instructions for Claude Code

## Project Overview
News Analyser is a full-stack web platform that aggregates news from 13+ Indian and international
sources, classifies articles by interest category and sentiment (Positive / Negative / Neutral),
and serves two target audiences:

1. **Students preparing for competitive exams** (UPSC, SSC, CAT, state PSCs) — need current
   affairs coverage across Politics, Economy, Science, Agriculture, and International topics.
2. **Investors and traders** — need Share Market, Economy, IT, Business, and Global news with
   sentiment-aware filtering.

Key features: multi-source aggregation, sentiment classification, historical browsing (up to 1
year back), and a 10-question MCQ "Test Your Knowledge" quiz feature.

Platform tone: **Motivating and subtle.** See `.claude/rules/design-guidelines.md §1` for details.

---

## Tech Stack

### Frontend
| Layer          | Technology                       | Version  |
|----------------|----------------------------------|----------|
| Framework      | React                            | 18.x     |
| Language       | TypeScript                       | 5.x      |
| Styling        | TailwindCSS                      | 3.x      |
| Routing        | React Router                     | v6       |
| Server State   | TanStack Query (React Query)     | v5       |
| Client State   | Zustand                          | v4       |
| HTTP Client    | Axios                            | 1.x      |
| Icons          | Lucide React                     | latest   |
| Build Tool     | Vite                             | 5.x      |
| Testing        | Vitest + React Testing Library   | latest   |
| A11y Testing   | jest-axe                         | latest   |
| API Mocking    | MSW (Mock Service Worker)        | v2       |

### Backend
| Layer          | Technology                       | Version  |
|----------------|----------------------------------|----------|
| Framework      | Spring Boot                      | 3.2.x    |
| Language       | Java                             | 21 (LTS) |
| Build Tool     | Maven                            | 3.9.x    |
| ORM            | Spring Data JPA / Hibernate      | 6.x      |
| Database       | PostgreSQL                       | 16.x     |
| DB Migrations  | Flyway                           | 9.x      |
| Connection Pool| HikariCP                         | bundled  |
| HTML Scraping  | Jsoup                            | 1.17.x   |
| RSS Parsing    | Rome                             | 2.1.x    |
| NLP/Sentiment  | Stanford CoreNLP                 | 4.5.x    |
| Cache (dev)    | Caffeine                         | 3.x      |
| Cache (prod)   | Redis via Spring Data Redis      | 7.x      |
| API Docs       | SpringDoc OpenAPI (Swagger UI)   | 2.x      |
| Security       | Spring Security + Bucket4j       | 6.x / 8.x|
| Utilities      | Lombok, MapStruct, Guava         | latest   |
| Testing        | JUnit 5 + Mockito + Testcontainers| latest  |

---

## Repository Structure

```
news-analyser/                              ← project root (CLAUDE.md is here)
├── CLAUDE.md                               ← YOU ARE HERE
├── .claude/
│   ├── agents/
│   │   ├── frontend-agent.md              ← React agent instructions
│   │   └── backend-agent.md               ← Spring Boot agent instructions
│   └── rules/
│       ├── design-guidelines.md           ← Design system, colours, typography
│       ├── frontend-development.md        ← Frontend code rules and patterns
│       └── backend-development.md         ← Backend code rules and patterns
├── news-analyser-frontend/                 ← React application (Vite)
│   ├── src/
│   │   ├── app/                           ← Router, store, App.tsx
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── ui/                        ← Primitives: Button, Input, Badge...
│   │   │   ├── layout/                    ← NavBar, Sidebar, Footer
│   │   │   └── shared/                    ← NewsCard, SentimentBadge, CategoryChip
│   │   ├── features/
│   │   │   ├── news/
│   │   │   ├── quiz/
│   │   │   ├── categories/
│   │   │   └── historical/
│   │   ├── lib/                           ← apiClient, utils, constants
│   │   └── pages/                         ← Route-level page components
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   └── package.json
└── news-analyser-backend/                  ← Spring Boot application
    ├── src/main/java/com/newsanalyser/
    │   ├── controller/
    │   ├── service/
    │   ├── repository/
    │   ├── model/
    │   ├── dto/
    │   ├── scraper/sources/
    │   ├── sentiment/
    │   ├── scheduler/
    │   ├── exception/
    │   └── config/
    ├── src/main/resources/
    │   ├── application.yml
    │   └── db/migration/
    └── pom.xml
```

---

## How to Use the Agents

### For any React / frontend work:
```
@frontend-agent [your task description]
```
The frontend agent follows `.claude/rules/design-guidelines.md` and
`.claude/rules/frontend-development.md` automatically. It handles all component creation,
hooks, routing, state management, and testing.

### For any Java / backend work:
```
@backend-agent [your task description]
```
The backend agent follows `.claude/rules/backend-development.md` automatically. It handles
all controller/service/repository implementation, scraping, sentiment analysis, scheduling,
and testing.

**Do not mix agents.** If a task spans both frontend and backend (e.g., "add a new filter"),
break it into two tasks: one for each agent.

---

## Setup & Running

### Frontend
```bash
cd news-analyser-frontend
npm install
npm run dev          # Start Vite dev server at http://localhost:5173
npm run build        # Production build
npm test             # Run Vitest tests
npm run test:coverage
```

### Backend
```bash
cd news-analyser-backend

# Requires PostgreSQL running locally (or Docker):
# docker run -d -p 5432:5432 -e POSTGRES_DB=newsanalyser -e POSTGRES_PASSWORD=secret postgres:16

mvn spring-boot:run -Dspring-boot.run.profiles=dev
# API available at http://localhost:8080
# Swagger UI at http://localhost:8080/swagger-ui.html

mvn test             # Run all tests (includes Testcontainers integration tests)
mvn package          # Build JAR
```

### Environment Variables
Copy `.env.example` files and fill in values before running:
```bash
# Frontend: news-analyser-frontend/.env
VITE_API_BASE_URL=http://localhost:8080/api/v1

# Backend: set as system env vars or in application-dev.yml
DB_HOST=localhost
DB_PORT=5432
DB_NAME=newsanalyser
DB_USERNAME=postgres
DB_PASSWORD=secret
REDIS_HOST=localhost
REDIS_PORT=6379
APP_FRONTEND_ORIGIN=http://localhost:5173
```

---

## News Sources

| Source                 | URL                                        |
|------------------------|--------------------------------------------|
| Times of India         | https://timesofindia.indiatimes.com/       |
| The Hindu              | https://www.thehindu.com/                  |
| Hindustan Times        | https://www.hindustantimes.com/            |
| BBC                    | https://www.bbc.com/                       |
| New York Times         | https://www.nytimes.com/                   |
| Wall Street Journal    | https://www.wsj.com/                       |
| The Guardian           | https://www.theguardian.com/international  |
| Telegraph              | https://www.telegraph.co.uk/               |
| Japan News (Yomiuri)   | https://japannews.yomiuri.co.jp/           |
| Fox News               | https://www.foxnews.com/                   |
| Straits Times          | https://www.straitstimes.com/global        |
| Al Jazeera             | https://www.aljazeera.com/                 |
| People's Daily         | https://en.people.cn/                      |

---

## Interest Categories

| Category             | Target Audience        |
|----------------------|------------------------|
| Share Market         | Investors              |
| Agriculture Sector   | Students, Investors    |
| Manufacturing Sector | Students, Investors    |
| IT Sector            | Students, Investors    |
| Healthcare Sector    | Students, Investors    |
| Hospitality Sector   | Students, Investors    |
| Education Sector     | Students               |
| Indian Politics      | Students               |
| Global Politics      | Students               |
| Entertainment        | Students               |
| Fashion              | Students               |
| Sports               | Students               |
| Environment          | Students               |
| Economics            | Students, Investors    |

---

## Feature Implementation Status

| Feature                                      | Status  |
|----------------------------------------------|---------|
| Interest selection page (14 categories)      | TODO    |
| News feed with category + sentiment filters  | TODO    |
| Multi-source aggregation (13+ sources)       | TODO    |
| Sentiment classification (Pos/Neg/Neutral)   | TODO    |
| Historical browsing (up to 1 year)           | TODO    |
| Test Your Knowledge quiz (10 MCQs)           | TODO    |
| Responsive design (mobile + web)             | TODO    |
| PostgreSQL persistence + Flyway migrations   | TODO    |
| Caffeine cache (dev) / Redis cache (prod)    | TODO    |
| Scheduled scraping (every 30 min)            | TODO    |
| Nightly historical snapshots                 | TODO    |
| Swagger UI API docs                          | TODO    |
| Rate limiting (Bucket4j)                     | TODO    |

---

## Key Architectural Decisions

| Decision                                    | Rationale                                                         |
|---------------------------------------------|-------------------------------------------------------------------|
| Java 21 + Spring Boot 3.2                   | LTS Java, virtual threads available, modern Spring features       |
| PostgreSQL over MySQL                       | Better full-text search, JSONB support for future use             |
| Stanford CoreNLP over OpenNLP               | Higher accuracy for news sentiment; one-time model load           |
| TanStack Query for server state             | Less boilerplate, built-in caching, background refetch            |
| Zustand over Redux Toolkit                  | Simpler for small global state (categories, date, theme)          |
| RSS-first scraping                          | More reliable, respects publisher intent, no HTML breakage        |
| Flyway for migrations                       | Version-controlled schema, no `ddl-auto` surprises in production  |
| Feature-based frontend folder structure     | Scales better than type-based as features grow                    |
| Caffeine (dev) + Redis (prod)               | No Redis dependency for local development                         |
| Bucket4j for rate limiting                  | Pure Java, no Redis required for rate limiting in dev             |

---

## Critical Rules for Claude Code

1. **Always re-read the relevant rule file before starting any implementation task.** Do not rely
   on memory of the rules — re-read the specific section for the task domain.

2. **Never invent a new design token.** If `design-guidelines.md` does not define a colour or
   spacing value for your use case, use the closest existing token and note the gap.

3. **The API contract in `backend-development.md §3.2` is the single source of truth** for
   frontend-backend integration. If a new endpoint is needed, update that section first.

4. **Sentiment colours carry semantic meaning.** Never reuse `--color-sentiment-positive` for
   anything unrelated to sentiment classification.

5. **Both target audiences must be served.** When prioritising features, ensure category coverage
   for both students and investors is maintained.

6. **All news source scrapers must respect `robots.txt`.** This is a legal and ethical requirement.
   See `backend-development.md §4.2 Rule 1`.

7. **Historical data is read-only.** The `/historical` endpoint serves articles already in the
   database. It must never trigger a live scrape — only query existing records.
