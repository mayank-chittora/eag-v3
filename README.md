# News Analyser

An intelligent, full-stack application designed to scrape news articles across various configured sources, analyze their core sentiments (Positive, Neutral, Negative), and present them through an elegant, categorised card-based user interface. 

The application groups news by user defined categories, offering a continuous scrolling discovery feed rather than relying on overwhelming text walls. 

---

## 🎥 Demo Video

>[!NOTE]
>**Demo Video URL Placeholder:** Insert your video link here!
>
>[Watch Demo Video](#) *(Update this link)*

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

```bash
cd news-analyser-backend

# Compile and start the Spring Boot server
mvn clean spring-boot:run
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
