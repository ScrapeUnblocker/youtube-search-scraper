"""Unit tests for the CLI parser and renderers (offline)."""

import csv
import io
import json

from youtube_search_scraper.cli import _render_csv, _render_json, _render_table, build_parser
from youtube_search_scraper.models import Video


def _video(vid="a", views=1000):
    return Video(
        video_id=vid,
        title="Learn Python 🐍",
        url=f"https://www.youtube.com/watch?v={vid}",
        channel="chan",
        duration="10:00",
        duration_seconds=600,
        view_count="1,000 views",
        views=views,
        published_time="1 year ago",
        thumbnail_url="https://img",
        description_snippet="snippet",
        query="python",
    )


def test_parser_defaults():
    args = build_parser().parse_args(["python tutorial"])
    assert args.queries == ["python tutorial"]
    assert args.sort == "relevance"
    assert args.format == "json"
    assert args.limit is None


def test_parser_multiple_queries_and_flags():
    args = build_parser().parse_args(
        [
            "cats",
            "dogs",
            "--sort",
            "view_count",
            "--country",
            "US",
            "--limit",
            "5",
            "--format",
            "csv",
        ]
    )
    assert args.queries == ["cats", "dogs"]
    assert args.sort == "view_count"
    assert args.country == "US"
    assert args.limit == 5
    assert args.format == "csv"


def test_render_json_roundtrips():
    payload = json.loads(_render_json([_video()]))
    assert payload[0]["video_id"] == "a"
    assert payload[0]["views"] == 1000


def test_render_csv_has_header_and_row():
    text = _render_csv([_video("x")])
    rows = list(csv.DictReader(io.StringIO(text)))
    assert rows[0]["video_id"] == "x"
    assert rows[0]["channel"] == "chan"


def test_render_table_contains_title_and_url():
    text = _render_table([_video("y")])
    assert "Learn Python" in text
    assert "watch?v=y" in text
