"""Data model for a single YouTube search result and its parsing helpers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

# Fields written to CSV, in order. Kept explicit so the column layout is stable.
CSV_FIELDS = (
    "video_id",
    "title",
    "url",
    "channel",
    "duration",
    "duration_seconds",
    "view_count",
    "views",
    "published_time",
    "thumbnail_url",
    "description_snippet",
    "query",
)


def _clean(value: object) -> str | None:
    """Return a stripped string, or ``None`` for empty / missing values."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_views(view_count: str | None) -> int | None:
    """Turn a YouTube view-count label into an integer.

    ``"48,964,265 views"`` -> ``48964265``. Handles ``"1.2M views"`` style
    abbreviations too, and returns ``None`` for ``None`` / ``"No views"`` / live
    streams (which expose no view count on the search page).
    """
    text = _clean(view_count)
    if text is None:
        return None

    # Abbreviated forms such as "1.2M views" or "998K watching".
    match = re.search(r"([\d.]+)\s*([KMB])", text, re.IGNORECASE)
    if match:
        number = float(match.group(1))
        multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[match.group(2).upper()]
        return int(number * multiplier)

    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def parse_duration(duration: str | None) -> int | None:
    """Convert a ``H:MM:SS`` / ``MM:SS`` duration into total seconds.

    Returns ``None`` when the duration is missing (e.g. live radio streams).
    """
    text = _clean(duration)
    if text is None:
        return None

    parts = text.split(":")
    if not all(part.isdigit() for part in parts):
        return None

    seconds = 0
    for part in parts:
        seconds = seconds * 60 + int(part)
    return seconds


@dataclass
class Video:
    """A single video from a YouTube search results page."""

    video_id: str | None
    title: str | None
    url: str | None
    channel: str | None
    duration: str | None
    duration_seconds: int | None
    view_count: str | None
    views: int | None
    published_time: str | None
    thumbnail_url: str | None
    description_snippet: str | None
    query: str | None = None

    @classmethod
    def from_parsed_item(cls, item: dict, query: str | None = None) -> Video:
        """Build a :class:`Video` from one ScrapeUnblocker parsed_data item."""
        duration = _clean(item.get("duration"))
        view_count = _clean(item.get("view_count"))
        return cls(
            video_id=_clean(item.get("video_id")),
            title=_clean(item.get("title")),
            url=_clean(item.get("url")),
            channel=_clean(item.get("channel_name")),
            duration=duration,
            duration_seconds=parse_duration(duration),
            view_count=view_count,
            views=parse_views(view_count),
            published_time=_clean(item.get("published_time")),
            thumbnail_url=_clean(item.get("thumbnail_url")),
            description_snippet=_clean(item.get("description_snippet")),
            query=query,
        )

    def to_dict(self) -> dict:
        """Return a plain dict (handy for ``json.dumps``)."""
        return asdict(self)
