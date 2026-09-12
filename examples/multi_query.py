"""Collect results across several queries and de-duplicate by video id.

YouTube search returns roughly one page (~20 results) per query, so the way to
build a larger, unique dataset is to run several related queries and merge them.

    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/multi_query.py
"""

from youtube_search_scraper import YouTubeSearchScraper


def main() -> None:
    scraper = YouTubeSearchScraper(proxy_country="US")
    queries = ["lofi hip hop", "chillhop", "study beats"]

    videos = scraper.search_many(queries, sort="upload_date", limit=15)
    print(f"Collected {len(videos)} unique videos across {len(queries)} queries.\n")

    for video in videos[:20]:
        print(f"- [{video.published_time}] {video.title}  ({video.channel})")


if __name__ == "__main__":
    main()
