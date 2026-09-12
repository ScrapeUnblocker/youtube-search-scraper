"""youtube-search-scraper: clean YouTube search results as JSON.

Scrape YouTube search results into structured records - video id, title, URL,
channel, duration, view count, publish time, thumbnail and description snippet -
using the ScrapeUnblocker ``getPageSource`` parsed-data API. Handles anti-bot
protection for you and returns AI-parsed JSON instead of raw HTML.

Powered by ScrapeUnblocker: https://scrapeunblocker.com
"""

from __future__ import annotations

from .models import Video
from .scraper import SORT_PRESETS, YouTubeSearchScraper, search

__all__ = ["Video", "YouTubeSearchScraper", "search", "SORT_PRESETS", "__version__"]

__version__ = "0.1.0"
