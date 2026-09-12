"""Core scraping logic for YouTube search results.

Everything routes through the ScrapeUnblocker ``getPageSource`` parsed-data API
via the official ``scrapeunblocker`` Python SDK, so anti-bot protection is handled
upstream and you get AI-parsed JSON instead of raw HTML.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from urllib.parse import urlencode

from .models import Video

SEARCH_ENDPOINT = "https://www.youtube.com/results"

# Verified YouTube ``sp`` sort tokens. ``relevance`` is the default (no token).
# Any other filter combination can be passed through with ``sp=...`` directly.
SORT_PRESETS: dict[str, str | None] = {
    "relevance": None,
    "upload_date": "CAI=",
    "view_count": "CAMSAhAB",
}


def _default_transient_exceptions() -> tuple[type[BaseException], ...]:
    """Transient SDK errors worth retrying (import lazily; SDK is optional here)."""
    try:
        from scrapeunblocker import (  # type: ignore[attr-defined]
            BlockedError,
            RateLimitError,
            ScrapeTimeoutError,
            ServerError,
            UpstreamOutageError,
        )
    except Exception:  # pragma: no cover - SDK always present in real use
        return ()
    return (
        UpstreamOutageError,
        RateLimitError,
        ServerError,
        ScrapeTimeoutError,
        BlockedError,
    )


class YouTubeSearchScraper:
    """Scrape YouTube search result pages into :class:`Video` records.

    Parameters
    ----------
    client:
        A ``scrapeunblocker.Client`` (or any object exposing
        ``get_parsed(url, proxy_country=...)``). If omitted, a real client is
        constructed lazily, reading the ``SCRAPEUNBLOCKER_KEY`` env var.
    proxy_country:
        Optional ISO country code to route requests through (e.g. ``"US"``),
        which also localises YouTube results.
    max_retries:
        How many times to retry a request that fails with a transient error.
    """

    def __init__(
        self,
        client: object | None = None,
        *,
        proxy_country: str | None = None,
        max_retries: int = 3,
        retry_backoff: float = 1.5,
        retry_on: tuple[type[BaseException], ...] | None = None,
        sleep: object = time.sleep,
    ) -> None:
        self._client = client
        self.proxy_country = proxy_country
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.retry_on = _default_transient_exceptions() if retry_on is None else retry_on
        self._sleep = sleep

    @property
    def client(self) -> object:
        """The underlying ScrapeUnblocker client, created on first use."""
        if self._client is None:
            from scrapeunblocker import Client  # imported lazily so tests need no key

            self._client = Client()
        return self._client

    def build_search_url(
        self,
        query: str,
        *,
        sort: str = "relevance",
        sp: str | None = None,
    ) -> str:
        """Build a YouTube search URL for ``query``.

        ``sort`` selects one of :data:`SORT_PRESETS`; an explicit ``sp`` token
        overrides it (use this for advanced filter combinations).
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        params: list[tuple[str, str]] = [("search_query", query.strip())]
        token = sp
        if token is None:
            if sort not in SORT_PRESETS:
                raise ValueError(
                    f"unknown sort {sort!r}; choose from {', '.join(SORT_PRESETS)} or pass sp="
                )
            token = SORT_PRESETS[sort]
        if token:
            params.append(("sp", token))
        return f"{SEARCH_ENDPOINT}?{urlencode(params)}"

    def _get_parsed(self, url: str) -> dict:
        """Call the SDK with retry on transient failures; return the data dict."""
        kwargs = {}
        if self.proxy_country:
            kwargs["proxy_country"] = self.proxy_country

        attempt = 0
        while True:
            try:
                result = self.client.get_parsed(url, **kwargs)
                break
            except self.retry_on:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                self._sleep(self.retry_backoff * attempt)

        # The SDK returns an object with a ``.data`` attribute; also accept a
        # plain dict so the scraper is easy to drive in tests.
        data = getattr(result, "data", None)
        if data is None and isinstance(result, dict):
            data = result.get("data")
        return data or {}

    def search(
        self,
        query: str,
        *,
        sort: str = "relevance",
        sp: str | None = None,
        limit: int | None = None,
    ) -> list[Video]:
        """Scrape a single query and return a list of :class:`Video`.

        YouTube search returns roughly one page (about 20 results) per query and
        exposes no next-page cursor, so ``limit`` simply trims the page. Use
        :meth:`search_many` to collect across several queries.
        """
        url = self.build_search_url(query, sort=sort, sp=sp)
        data = self._get_parsed(url)
        items = data.get("items") or []
        videos = [Video.from_parsed_item(item, query=query) for item in items]
        if limit is not None:
            videos = videos[:limit]
        return videos

    def search_many(
        self,
        queries: Iterable[str],
        *,
        sort: str = "relevance",
        sp: str | None = None,
        limit: int | None = None,
    ) -> list[Video]:
        """Scrape several queries and merge them, de-duplicating by video id.

        The first query that surfaces a given video wins (its ``query`` field is
        kept). ``limit`` applies per query before merging.
        """
        seen: set[str] = set()
        merged: list[Video] = []
        for query in queries:
            for video in self.search(query, sort=sort, sp=sp, limit=limit):
                key = video.video_id or video.url
                if key is None or key in seen:
                    continue
                seen.add(key)
                merged.append(video)
        return merged


def search(
    query: str,
    *,
    proxy_country: str | None = None,
    sort: str = "relevance",
    sp: str | None = None,
    limit: int | None = None,
    client: object | None = None,
) -> list[Video]:
    """Convenience one-shot search using a default scraper.

    >>> from youtube_search_scraper import search
    >>> videos = search("python tutorial", sort="view_count", limit=5)
    """
    scraper = YouTubeSearchScraper(client=client, proxy_country=proxy_country)
    return scraper.search(query, sort=sort, sp=sp, limit=limit)


__all__ = ["YouTubeSearchScraper", "search", "SORT_PRESETS"]
