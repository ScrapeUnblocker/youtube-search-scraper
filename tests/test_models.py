"""Unit tests for parsing helpers and the Video model (offline, no API calls)."""

from youtube_search_scraper.models import Video, parse_duration, parse_views


def test_parse_views_full_number():
    assert parse_views("48,964,265 views") == 48964265


def test_parse_views_abbreviated():
    assert parse_views("1.2M views") == 1_200_000
    assert parse_views("998K watching") == 998_000


def test_parse_views_missing():
    assert parse_views(None) is None
    assert parse_views("") is None
    assert parse_views("No views") is None


def test_parse_duration_hms():
    assert parse_duration("6:14:07") == 6 * 3600 + 14 * 60 + 7


def test_parse_duration_ms():
    assert parse_duration("10:30") == 630


def test_parse_duration_missing_or_junk():
    assert parse_duration(None) is None
    assert parse_duration("LIVE") is None


def test_from_parsed_item_full():
    item = {
        "video_id": "abc123",
        "title": "Learn Python",
        "url": "https://www.youtube.com/watch?v=abc123",
        "channel_name": "freeCodeCamp.org",
        "duration": "4:26:52",
        "view_count": "49,264,417 views",
        "published_time": "8 years ago",
        "thumbnail_url": "https://i.ytimg.com/vi/abc123/hq720.jpg",
        "description_snippet": "This course...",
    }
    video = Video.from_parsed_item(item, query="python")
    assert video.video_id == "abc123"
    assert video.channel == "freeCodeCamp.org"
    assert video.views == 49264417
    assert video.duration_seconds == 4 * 3600 + 26 * 60 + 52
    assert video.query == "python"


def test_from_parsed_item_live_stream_nulls():
    # Live radio streams expose no duration / views / publish time.
    item = {
        "video_id": "live1",
        "title": "lofi hip hop radio",
        "url": "https://www.youtube.com/watch?v=live1",
        "channel_name": "Lofi Girl",
        "duration": None,
        "view_count": None,
        "published_time": None,
        "thumbnail_url": None,
        "description_snippet": None,
    }
    video = Video.from_parsed_item(item)
    assert video.duration is None
    assert video.duration_seconds is None
    assert video.views is None
    assert video.query is None
