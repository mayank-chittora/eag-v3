# News Analyser

An intelligent, full-stack application designed to scrape news articles across various configured sources, analyze their core sentiments (Positive, Neutral, Negative), and present them through an elegant, categorised card-based user interface.

The application groups news by user defined categories, offering a continuous scrolling discovery feed rather than relying on overwhelming text walls. An AI-powered **Generate Summary** feature provides a Gemini-streamed daily digest and stock market impact analysis, delivered in a Claude-like drawer directly within the feed.

---

## 🎥 Demo Video

>[Watch Demo Video](https://youtu.be/yTpeT_BZcPY)

---

## 🚀 Tech Stack

### Frontend (`news-analyser-frontend`)
* **Framework:** React + TypeScript (Bootstrapped via Vite)
* **Styling:** TailwindCSS for clean, utility-first design and native component grouping.
* **Data Fetching & State:** React Query (TanStack Query) for declarative caching and network syncing.
* **Date Utilities:** `date-fns` for standardizing native parsing between frontend states and API strings.
* **Icons:** `lucide-react`

### Backend (`news-analyser-backend`)
* **Framework:** Spring Boot 3.2 on **Java 21**
* **Database:** PostgreSQL (with Flyway for schema migrations)
* **API Documentation:** OpenAPI / Swagger UI (`springdoc-openapi`)
* **Scraping Engine:** Jsoup (for raw HTML mapping) & ROME (for RSS feeds)
* **Rate Limiting:** Bucket4J to prevent API abuse
* **Local Caching:** Caffeine to keep database fetches optimal
* **AI / LLM:** Google Gemini (`gemini-2.5-flash`) via REST for daily summary and market analysis, streamed as SSE

---

## ⚙️ How to Run Locally

To get the full application up and running on your local machine, you will need to start both the Spring Boot Backend server, and the Vite Frontend listener separately.

### Prerequisites
- Node.js (v18+)
- Java JDK 21+
- Maven
- PostgreSQL running locally (or via Docker)

### 1. Backend Setup

From the root repository branch, navigate to the backend service. Ensure your PostgreSQL credentials locally align with what's placed in `src/main/resources/application.yml`.

**Gemini API key (required for the Generate Summary feature):** Create `news-analyser-backend/src/main/resources/application-local.yml` (this file is gitignored) and add:

```yaml
gemini:
  api-key: YOUR_GEMINI_API_KEY_HERE
```

The backend loads this file automatically when started with the `local` profile (see the run command below).

```bash
cd news-analyser-backend

# Compile and start the Spring Boot server (dev + local profiles)
mvn clean spring-boot:run -Dspring-boot.run.profiles=dev,local
```
*The backend server will instantiate on port **`8080`**. You can view Swagger documentation at: `http://localhost:8080/swagger-ui.html`*

### 2. Frontend Setup

In a new terminal window from the root, navigate to the frontend directory:

```bash
cd news-analyser-frontend

# Install node dependencies
npm install

# Start the Vite development environment
npm run dev
```

*The frontend application will boot up at **`http://localhost:5173`**. Enjoy the feed!*

---

## ✨ Generate Summary Feature

Clicking **"Generate Summary"** in the news feed opens a side drawer that streams an AI-generated daily digest directly from Google Gemini.

### What it does
1. **Daily News Summary** — Gemini reads today's articles (filtered by your selected categories) and produces a concise, structured briefing.
2. **Stock Market Impact Analysis** — A second Gemini call analyses the same articles specifically for market implications, highlighting sectors and sentiment relevant to investors.

Both responses are streamed token-by-token in a Claude-like drawer so you see content as it is generated — no waiting for the full response.

### How it works

| Layer | Detail |
|---|---|
| Endpoint | `GET /api/v1/summary` (SSE) |
| Streaming protocol | Server-Sent Events — native `EventSource` (not Axios) |
| SSE event types | `thinking` · `tool_call` · `tool_result` · `text_chunk` · `done` · `error` |
| LLM model | `gemini-2.5-flash` |
| Timeout | 5 minutes (`SseEmitter(300_000L)`) — both Gemini calls together can take ~2 min |
| Logs | LLM interactions logged to `logs/llm-responses.log` |

### Key files

**Backend**
- `config/GeminiConfig.java` — Gemini REST client configuration
- `config/GeminiClient.java` — low-level REST calls to the Gemini API
- `service/GeminiSummaryServiceImpl.java` — orchestrates the two Gemini calls
- `controller/SummaryController.java` — SSE endpoint
- `dto/request/SummaryRequest.java`, `dto/response/SseEvent.java`

**Frontend**
- `features/news/components/SummaryDrawer.tsx` — streaming drawer UI
- `features/news/hooks/useSummaryStream.ts` — `EventSource` hook; routes `text_chunk` events to the correct section
- `features/news/services/summaryService.ts` — manages the SSE connection

### Configuration

| Setting | Location | Notes |
|---|---|---|
| `gemini.api-key` | `application-local.yml` (gitignored) | Required; obtain from Google AI Studio |
| Active profiles | `spring.profiles.active=dev,local` | Loads `application-local.yml` |
