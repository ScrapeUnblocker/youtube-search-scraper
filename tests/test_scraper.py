"""Unit tests for the scraper (SDK fully mocked - no API credit spent)."""

import pytest

from youtube_search_scraper.scraper import SORT_PRESETS, YouTubeSearchScraper


class Transient(Exception):
    """Stand-in for a transient SDK error (e.g. UpstreamOutageError)."""


class ParsedResult:
    """Mimics the SDK's parsed-result object with a ``.data`` attribute."""

    def __init__(self, items):
        self.data = {"items": items, "total": len(items), "next_page": None}


def _item(vid, title="t", views="1,000 views"):
    return {
        "video_id": vid,
        "title": title,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "channel_name": "chan",
        "duration": "10:00",
        "view_count": views,
        "published_time": "1 year ago",
        "thumbnail_url": "https://img",
        "description_snippet": "snippet",
    }


class FakeClient:
    """Records the URLs requested and returns canned parsed results."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def get_parsed(self, url, **kwargs):
        self.calls.append((url, kwargs))
        result = self._results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_build_search_url_encodes_query_and_relevance_has_no_sp():
    scraper = YouTubeSearchScraper(client=FakeClient([]))
    url = scraper.build_search_url("python tutorial")
    assert url == "https://www.youtube.com/results?search_query=python+tutorial"


def test_build_search_url_applies_sort_token():
    scraper = YouTubeSearchScraper(client=FakeClient([]))
    url = scraper.build_search_url("cats", sort="view_count")
    assert "sp=" + "CAMSAhAB" in url
    assert SORT_PRESETS["view_count"] == "CAMSAhAB"


def test_build_search_url_raw_sp_overrides_sort():
    scraper = YouTubeSearchScraper(client=FakeClient([]))
    url = scraper.build_search_url("cats", sort="view_count", sp="CUSTOM")
    assert "sp=CUSTOM" in url


def test_build_search_url_rejects_empty_and_bad_sort():
    scraper = YouTubeSearchScraper(client=FakeClient([]))
    with pytest.raises(ValueError):
        scraper.build_search_url("   ")
    with pytest.raises(ValueError):
        scraper.build_search_url("x", sort="nope")


def test_search_shapes_items_and_passes_country():
    client = FakeClient([ParsedResult([_item("a"), _item("b")])])
    scraper = YouTubeSearchScraper(client=client, proxy_country="US")
    videos = scraper.search("q")
    assert [v.video_id for v in videos] == ["a", "b"]
    assert videos[0].views == 1000
    # proxy_country must be forwarded to the SDK.
    assert client.calls[0][1] == {"proxy_country": "US"}


def test_search_limit_trims_page():
    client = FakeClient([ParsedResult([_item("a"), _item("b"), _item("c")])])
    scraper = YouTubeSearchScraper(client=client)
    assert len(scraper.search("q", limit=2)) == 2


def test_search_handles_missing_items_key():
    class Empty:
        data = {"total": 0}

    scraper = YouTubeSearchScraper(client=FakeClient([Empty()]))
    assert scraper.search("q") == []


def test_search_many_dedupes_by_video_id():
    client = FakeClient(
        [
            ParsedResult([_item("a"), _item("b")]),
            ParsedResult([_item("b"), _item("c")]),  # 'b' repeats across queries
        ]
    )
    scraper = YouTubeSearchScraper(client=client)
    videos = scraper.search_many(["q1", "q2"])
    assert [v.video_id for v in videos] == ["a", "b", "c"]
    assert videos[1].query == "q1"  # first query to surface 'b' wins


def test_retry_then_success():
    sleeps = []
    client = FakeClient([Transient("boom"), ParsedResult([_item("a")])])
    scraper = YouTubeSearchScraper(
        client=client,
        retry_on=(Transient,),
        max_retries=3,
        sleep=sleeps.append,
    )
    videos = scraper.search("q")
    assert [v.video_id for v in videos] == ["a"]
    assert len(sleeps) == 1  # one retry backoff


def test_retry_exhausted_reraises():
    client = FakeClient([Transient("1"), Transient("2"), Transient("3"), Transient("4")])
    scraper = YouTubeSearchScraper(
        client=client,
        retry_on=(Transient,),
        max_retries=2,
        sleep=lambda _s: None,
    )
    with pytest.raises(Transient):
        scraper.search("q")
