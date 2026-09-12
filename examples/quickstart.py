"""Quickstart: search YouTube and print the results as JSON.

export SCRAPEUNBLOCKER_KEY=your_key_here   # get one at scrapeunblocker.com
python examples/quickstart.py
"""

import json

from youtube_search_scraper import YouTubeSearchScraper


def main() -> None:
    scraper = YouTubeSearchScraper(proxy_country="US")
    videos = scraper.search("python tutorial", limit=5)

    for video in videos:
        print(f"- {video.title}  ({video.channel}, {video.view_count})")

    print("\nAs JSON:")
    print(json.dumps([v.to_dict() for v in videos], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
