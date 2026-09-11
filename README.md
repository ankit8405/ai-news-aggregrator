# AI News Aggregator

A daily, personalized AI-news pipeline. It pulls fresh content from YouTube channels, the OpenAI blog, and Anthropic's news/research/engineering feeds, uses OpenAI models to summarize and rank everything against a personal interest profile, and emails a curated top-N digest as a styled HTML email. It runs as a scheduled cron job on Render.

## How it works

The pipeline runs in stages (`app/daily_runner.py -> run_daily_pipeline`):

0. **Ensure the schema** — create any missing tables or columns (idempotent) so a fresh database self-initializes.
1. **Scrape** — collect new items published in the last `N` hours and store them in PostgreSQL:
   - YouTube channel RSS feeds (`app/scrapers/youtube.py`)
   - OpenAI news RSS (`app/scrapers/openai.py`)
   - Anthropic news / research / engineering RSS (`app/scrapers/anthropic.py`)
2. **Convert Anthropic articles to Markdown** — `html-to-markdown` renders each article page so summaries use the full content, not just the RSS excerpt.
3. **Fetch YouTube transcripts** — attach transcripts to the scraped videos via `youtube-transcript-api`.
4. **Generate digests** — `gpt-4o-mini` writes a short title and a 2–3 sentence summary for each article (`app/agent/digest.py`).
5. **Curate & email** — the curator agent ranks the recent digests against the user profile (`app/agent/curator.py`), the email agent writes a personalized introduction (`app/agent/email.py`), and the top-N articles are sent as a styled HTML email over Gmail SMTP.

```
scrape ─▶ markdown ─▶ transcripts ─▶ digest (LLM) ─▶ rank (LLM) ─▶ email
           html-to      yt-api        summarized      scored       top-N digest
           -markdown
```

## Tech stack

Python (managed with [uv](https://docs.astral.sh/uv/)), PostgreSQL via SQLAlchemy ORM (a local instance runs through Docker), OpenAI `gpt-4o-mini` with structured outputs for digests and ranking, `feedparser` / `requests` / `html-to-markdown` / `youtube-transcript-api` for scraping, and Gmail SMTP for email delivery. Containerized with Docker and deployed as a scheduled cron job on Render.

## Project structure

```
.
├── main.py                          # CLI entry point
├── app/                             # application package
│   ├── __init__.py
│   ├── config.py                    # YOUTUBE_CHANNELS to follow
│   ├── daily_runner.py              # pipeline orchestrator
│   ├── runner.py                    # run_scrapers(): scrape + persist
│   ├── .env.example                 # environment variable template
│   ├── agent/                       # LLM agents (OpenAI)
│   │   ├── __init__.py
│   │   ├── base.py                  #   shared OpenAI client base
│   │   ├── curator.py               #   rank digests against the profile
│   │   ├── digest.py                #   summarize one article -> digest
│   │   └── email.py                 #   write the email introduction
│   ├── scrapers/                    # RSS scrapers
│   │   ├── __init__.py
│   │   ├── base.py                  #   BaseScraper: shared fetch + Article model
│   │   ├── youtube.py               #   channel RSS + video transcripts
│   │   ├── openai.py                #   OpenAI news RSS
│   │   └── anthropic.py             #   Anthropic news/research/engineering RSS
│   ├── services/                    # batch orchestration + SMTP sending
│   │   ├── __init__.py
│   │   ├── base.py                  #   BaseProcessService: shared batch loop
│   │   ├── email.py                 #   SMTP sending + HTML rendering
│   │   ├── process_anthropic.py     #   article URL -> markdown
│   │   ├── process_youtube.py       #   attach video transcripts
│   │   ├── process_digest.py        #   generate one digest per article
│   │   ├── process_curator.py       #   rank recent digests
│   │   └── process_email.py         #   generate + send the email digest
│   ├── database/                    # persistence
│   │   ├── __init__.py
│   │   ├── connection.py            #   SQLAlchemy engine + session
│   │   ├── models.py                #   ORM models
│   │   ├── repository.py            #   data-access layer
│   │   ├── create_tables.py         #   create/update tables
│   │   └── check_conn.py            #   database connection checker
│   └── profiles/
│       └── user_profile.py          # interests + preferences for personalization
├── docker/
│   └── docker-compose.yml           # local PostgreSQL 17
├── Dockerfile                       # image used for Render deployment
├── render.yaml                      # Render blueprint (cron job + Postgres)
├── pyproject.toml                   # project metadata & dependencies
├── uv.lock                          # locked dependency versions
├── .dockerignore
├── .gitignore
├── README.md
└── ai-news-aggregator.code-workspace
```

## Getting started

### Prerequisites

- **Python**
- **[uv](https://docs.astral.sh/uv/)** — dependency & environment manager
- **Docker** — to run PostgreSQL locally

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

Create your `.env` from the template and fill in real values:

```bash
cp app/.env.example app/.env
```

| Variable                          | Description                                                      |
| --------------------------------- | ---------------------------------------------------------------- |
| `OPENAI_API_KEY`                  | OpenAI API key (digests, ranking, email intro).                  |
| `MY_EMAIL`                        | Gmail address the digest is sent from and to.                    |
| `APP_PASSWORD`                    | Gmail **App Password** (requires 2FA), not your login password.  |
| `POSTGRES_USER`                   | Postgres user (default `postgres`).                              |
| `POSTGRES_PASSWORD`               | Postgres password (default `postgres`).                          |
| `POSTGRES_DB`                     | Database name (default `ai_news_aggregator`).                    |
| `POSTGRES_HOST`                   | Postgres host (default `localhost`).                            |
| `POSTGRES_PORT`                   | Postgres port (default `5432`).                                 |
| `DATABASE_URL`                    | Full Postgres URL; overrides `POSTGRES_*`. Set automatically on Render. |
| `PROXY_USERNAME` / `PROXY_PASSWORD` | Webshare proxy, required for YouTube transcripts when YouTube blocks the host IP. |

> `.env` is git-ignored. Locally the app uses `POSTGRES_*`; on Render it uses the injected `DATABASE_URL`.

### 3. Start PostgreSQL

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 4. Create the database tables

```bash
uv run python -m app.database.create_tables
```

### 5. Run the pipeline

```bash
uv run python main.py            # defaults: last 24h, top 10 articles
uv run python main.py 48 15      # last 48h, top 15 articles
```

`main.py [hours] [top_n]` — `hours` windows the scrape and the ranking; `top_n` caps how many articles appear in the email. Exit code is `0` on success, `1` on failure.

## Deployment

The project is deployed to [Render](https://render.com) as a scheduled cron job, defined entirely in `render.yaml`:

- **Database** — a managed Render PostgreSQL instance (`ai-news-aggregator-db`). Its connection string is injected into the service as `DATABASE_URL`.
- **Cron job** — runs the Docker image daily at `30 2 * * *` (02:30 UTC / 08:00 IST) via `dockerCommand: python main.py`.
- **Secrets** — `OPENAI_API_KEY`, `MY_EMAIL`, and `APP_PASSWORD` are declared with `sync: false` and are set in the Render dashboard (never in the repo).

To deploy:

1. Push the repository to GitHub.
2. In Render, create a **Blueprint** pointing at the repo — Render reads `render.yaml` and provisions the database and cron job.
3. Provide the three secrets when prompted.
4. Trigger a run from the dashboard, or wait for the schedule.


## Configuration

- **Sources** — edit `app/config.py` (`YOUTUBE_CHANNELS`) to follow different YouTube channels.
- **Personalization** — edit `app/profiles/user_profile.py` (name, background, interests, preferences). The curator ranks articles against this profile.
- **Model** — `gpt-4o-mini` is set in each agent under `app/agent/`.

## Notes

- **Gmail App Password**: enable 2-Step Verification on the Google account, then create an App Password under *Security → App passwords*. Use that 16-character value for `APP_PASSWORD`.
- **YouTube transcripts** are rate-limited by YouTube. Without a proxy they may be unavailable (transcript-less videos are skipped). Supply `PROXY_USERNAME` / `PROXY_PASSWORD` (e.g. Webshare) to fetch transcripts reliably.
- **Idempotency**: each digest is stored once and marked `sent_at` after it is emailed, so a digest is never sent twice.
