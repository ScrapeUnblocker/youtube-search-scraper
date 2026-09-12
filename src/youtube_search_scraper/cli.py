"""Command-line interface for youtube-search-scraper."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys

from . import __version__
from .models import CSV_FIELDS, Video
from .scraper import SORT_PRESETS, YouTubeSearchScraper


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser (kept separate so it can be unit-tested)."""
    parser = argparse.ArgumentParser(
        prog="youtube-search",
        description="Scrape YouTube search results as clean JSON/CSV via ScrapeUnblocker.",
    )
    parser.add_argument("queries", nargs="+", help="one or more search queries")
    parser.add_argument(
        "--sort",
        choices=sorted(SORT_PRESETS),
        default="relevance",
        help="result ordering (default: relevance)",
    )
    parser.add_argument(
        "--sp",
        metavar="TOKEN",
        default=None,
        help="raw YouTube 'sp' filter token (overrides --sort for advanced filters)",
    )
    parser.add_argument(
        "--country",
        metavar="XX",
        default=None,
        help="ISO country code to route through and localise results (e.g. US)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="max results to keep per query",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv", "table"),
        default="json",
        help="output format (default: json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help="write to FILE instead of stdout",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="retries on transient errors (default: 3)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _render_json(videos: list[Video]) -> str:
    return json.dumps([v.to_dict() for v in videos], indent=2, ensure_ascii=False)


def _render_csv(videos: list[Video]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(CSV_FIELDS))
    writer.writeheader()
    for video in videos:
        writer.writerow(video.to_dict())
    return buffer.getvalue()


def _render_table(videos: list[Video]) -> str:
    lines = []
    for video in videos:
        views = f"{video.views:,}" if video.views is not None else "-"
        duration = video.duration or "live/-"
        lines.append(
            f"[{duration:>8}] {views:>14} views  {video.channel or '-'}\n"
            f"           {video.title or '-'}\n"
            f"           {video.url or '-'}"
        )
    return "\n".join(lines)


def _render(videos: list[Video], fmt: str) -> str:
    if fmt == "csv":
        return _render_csv(videos)
    if fmt == "table":
        return _render_table(videos)
    return _render_json(videos)


def main(argv: list[str] | None = None) -> int:
    # YouTube titles are full of emoji/non-ASCII; force UTF-8 stdout on consoles
    # (e.g. Windows cp1252) that would otherwise raise UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    args = build_parser().parse_args(argv)

    scraper = YouTubeSearchScraper(proxy_country=args.country, max_retries=args.max_retries)
    try:
        videos = scraper.search_many(args.queries, sort=args.sort, sp=args.sp, limit=args.limit)
    except Exception as exc:  # surface a clean one-line error, not a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rendered = _render(videos, args.format)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as handle:
            handle.write(rendered)
        print(f"wrote {len(videos)} result(s) to {args.output}", file=sys.stderr)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
