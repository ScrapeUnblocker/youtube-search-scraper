# youtube-search-scraper

[![CI](https://github.com/ScrapeUnblocker/youtube-search-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/ScrapeUnblocker/youtube-search-scraper/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Scrape **YouTube search results** as clean, structured JSON or CSV — video id,
title, URL, channel, duration, view count, publish time, thumbnail and
description snippet — for any query and market. Ships a CLI and a small Python
library.

> **Powered by [ScrapeUnblocker](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos).**
> YouTube is rendered behind heavy anti-bot protection, so this project fetches
> pages through the ScrapeUnblocker `getPageSource` **parsed-data** API: it
> returns AI-parsed JSON instead of raw HTML, so there are no brittle CSS
> selectors to maintain.

## Features

- 🔎 Search any query and get a list of typed `Video` records.
- 🧹 Clean fields: numeric `views` and `duration_seconds` parsed alongside the
  original display strings; `None` for values YouTube omits (e.g. live streams).
- ↕️ Verified sort presets: `relevance`, `upload_date`, `view_count` — plus a
  raw `sp=` passthrough for advanced YouTube filters.
- 🌍 Country targeting to localise results (`--country US`).
- 🧺 Multi-query collection with automatic de-duplication by video id.
- 📤 Output as JSON, CSV, or a readable table.
- 🔁 Automatic retry on transient upstream errors.
- ✅ Offline unit tests that mock the SDK — no API credit spent in CI.

## Install

```bash
pip install .
# or, for development (tests + linter):
pip install -e ".[dev]"
```

Set your API key (get one at
[scrapeunblocker.com](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)):

```bash
export SCRAPEUNBLOCKER_KEY=your_key_here   # see .env.example
```

## CLI usage

```bash
# Top results as JSON
youtube-search "python tutorial" --limit 5

# Most-viewed first, US results, export to CSV
youtube-search "machine learning" --sort view_count --country US --format csv -o ml.csv

# Newest first across several queries, merged and de-duplicated
youtube-search "lofi hip hop" "chillhop" "study beats" --sort upload_date --limit 15 --format table
```

```
usage: youtube-search [-h] [--sort {relevance,upload_date,view_count}] [--sp TOKEN]
                      [--country XX] [--limit LIMIT] [--format {json,csv,table}]
                      [--output FILE] [--max-retries MAX_RETRIES] [--version]
                      queries [queries ...]
```

## Library usage

```python
from youtube_search_scraper import YouTubeSearchScraper

scraper = YouTubeSearchScraper(proxy_country="US")

# One query
videos = scraper.search("python tutorial", sort="view_count", limit=5)
for v in videos:
    print(v.title, v.views, v.url)

# Several queries, merged and de-duplicated by video id
videos = scraper.search_many(["lofi hip hop", "chillhop"], sort="upload_date")
```

Or the one-shot helper:

```python
from youtube_search_scraper import search

videos = search("data science", sort="upload_date", limit=10)
```

### Example output

```json
[
  {
    "video_id": "rfscVS0vtbw",
    "title": "Learn Python - Full Course for Beginners [Tutorial]",
    "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
    "channel": "freeCodeCamp.org",
    "duration": "4:26:52",
    "duration_seconds": 16012,
    "view_count": "49,264,417 views",
    "views": 49264417,
    "published_time": "8 years ago",
    "thumbnail_url": "https://i.ytimg.com/vi/rfscVS0vtbw/hq720.jpg",
    "description_snippet": "This course will give you a full introduction...",
    "query": "python tutorial"
  }
]
```

## How it works & limits

- Each query maps to a YouTube `results?search_query=...` page, fetched through
  ScrapeUnblocker's parsed-data API.
- YouTube search returns roughly **one page (~20 results)** per query and does
  not expose a next-page cursor, so there is no deep pagination. To build a
  larger, unique dataset, run several related queries and let `search_many`
  merge and de-duplicate them.
- Live streams and some entries have no duration / view count on the search
  page; those fields come back as `null`.

## Project layout

```
src/youtube_search_scraper/
  __init__.py      # package exports + __version__
  models.py        # Video dataclass + view/duration parsing
  scraper.py       # YouTubeSearchScraper: URL building, retry, shaping
  cli.py           # argparse CLI (youtube-search)
examples/          # runnable quickstart / CSV export / multi-query scripts
tests/             # offline unit tests (SDK mocked)
```

## Development

```bash
make install   # editable install with dev deps
make lint      # ruff check
make format    # ruff format
make test      # pytest (offline, no API key needed)
```

## Links

- Website: https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos
- Docs: https://docs.scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos

## License

[MIT](LICENSE) © 2026 ScrapeUnblocker
