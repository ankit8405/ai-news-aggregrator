# AI News Aggregator

A daily, personalized AI-news pipeline. It pulls fresh content from YouTube channels, the OpenAI blog, and Anthropic's news/research/engineering feeds, uses OpenAI models to summarize and rank everything against a personal interest profile, and emails a curated top-N digest as a styled HTML email.

## How it works

The pipeline runs in five stages (`app/daily_runner.py -> run_daily_pipeline`):

1. **Scrape** — collect new items published in the last `N` hours and store them in PostgreSQL:
   - YouTube channel RSS feeds (`app/scrapers/youtube.py`)
   - OpenAI news RSS (`app/scrapers/openai.py`)
   - Anthropic news / research / engineering RSS (`app/scrapers/anthropic.py`)
2. **Convert Anthropic articles to Markdown** — `docling` renders each article page to Markdown so summaries use the full content, not just the RSS excerpt.
3. **Fetch YouTube transcripts** — attach transcripts to the scraped videos via `youtube-transcript-api`.
4. **Generate digests** — `gpt-4o-mini` writes a short title and a 2–3 sentence summary for each article (`app/agent/digest.py`).
5. **Curate & email** — the curator agent ranks all recent digests against the user profile (`app/agent/curator.py`), the email agent writes a personalized introduction (`app/agent/email.py`), and the top-N articles are sent as a styled HTML email over Gmail SMTP.

```
scrape ─▶ markdown ─▶ transcripts ─▶ digest (LLM) ─▶ rank (LLM) ─▶ email
         (docling)    (yt-api)       summarized      scored        top-N digest
```

## Tech stack

Python (managed with [uv](https://docs.astral.sh/uv/)), PostgreSQL via SQLAlchemy ORM (a local instance is provided through Docker), OpenAI `gpt-4o-mini` with structured outputs for digests and ranking, `feedparser` / `requests` / `docling` / `youtube-transcript-api` for scraping, and Gmail SMTP for email delivery.

## Project structure

```
.
├── main.py                          # CLI entry point
├── app/                             # application package
│   ├── __init__.py
│   ├── config.py                    # YOUTUBE_CHANNELS to follow
│   ├── daily_runner.py              # 5-stage pipeline orchestrator
│   ├── runner.py                    # run_scrapers(): scrape + persist
│   ├── .env.example                 # environment variable template
│   ├── agent/                       # LLM agents (OpenAI)
│   │   ├── __init__.py
│   │   ├── curator.py               #   rank digests against the profile
│   │   ├── digest.py                #   summarize one article -> digest
│   │   └── email.py                 #   write the email introduction
│   ├── scrapers/                    # RSS scrapers (youtube / openai / anthropic)
│   │   ├── __init__.py
│   │   ├── youtube.py               #   channel RSS + video transcripts
│   │   ├── openai.py                #   OpenAI news RSS
│   │   └── anthropic.py             #   Anthropic news/research/engineering RSS
│   ├── services/                    # process_* orchestration + SMTP sending
│   │   ├── __init__.py
│   │   ├── email.py                 #   SMTP sending + HTML rendering
│   │   ├── process_anthropic.py     #   article URL -> markdown (docling)
│   │   ├── process_youtube.py       #   attach video transcripts
│   │   ├── process_digest.py        #   generate one digest per article
│   │   ├── process_curator.py       #   rank recent digests
│   │   └── process_email.py         #   generate + send the email digest
│   ├── database/                    # models, connection, repository, create_tables
│   │   ├── __init__.py
│   │   ├── connection.py            #   SQLAlchemy engine + session
│   │   ├── models.py                #   ORM models
│   │   ├── repository.py            #   data-access layer
│   │   └── create_tables.py         #   create tables script
│   └── profiles/
│       └── user_profile.py          # interests + preferences for personalization
├── docker/
│   └── docker-compose.yml           # PostgreSQL 17
├── pyproject.toml                   # project metadata & dependencies
├── uv.lock                          # locked dependency versions
├── README.md
├── .gitignore
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

| Variable            | Required | Description                                                        |
| ------------------- | -------- | ------------------------------------------------------------------ |
| `OPENAI_API_KEY`    | yes      | OpenAI API key (used for digests, ranking, and the email intro).   |
| `MY_EMAIL`          | yes      | Gmail address the digest is sent from and to.                      |
| `APP_PASSWORD`      | yes      | Gmail **App Password** (requires 2FA) — not your account password. |
| `POSTGRES_USER`     | yes      | Postgres user (default `postgres`).                                |
| `POSTGRES_PASSWORD` | yes      | Postgres password (default `postgres`).                            |
| `POSTGRES_DB`       | yes      | Database name (default `ai_news_aggregator`).                      |
| `POSTGRES_HOST`     | yes      | Postgres host (default `localhost`).                              |
| `POSTGRES_PORT`     | yes      | Postgres port (default `5432`).                                   |

> `.env` is git-ignored. Never commit real credentials.

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

## Configuration

- **Sources** — edit `app/config.py` (`YOUTUBE_CHANNELS`) to follow different YouTube channels.
- **Personalization** — edit `app/profiles/user_profile.py` (name, background, interests, preferences). The curator ranks articles against this profile.
- **Model** — `gpt-4o-mini` is set in each agent under `app/agent/`.

## Notes

- **Gmail App Password**: enable 2-Step Verification on the Google account, then create an App Password under *Security → App passwords*. Use that 16-character value for `APP_PASSWORD`.
- Each stage can be run on its own, e.g. `uv run python -m app.runner`, `uv run python -m app.services.process_digests`.
