"""Sort by view count and export the results to a CSV file.

export SCRAPEUNBLOCKER_KEY=your_key_here
python examples/export_csv.py
"""

import csv

from youtube_search_scraper import YouTubeSearchScraper
from youtube_search_scraper.models import CSV_FIELDS


def main() -> None:
    scraper = YouTubeSearchScraper(proxy_country="US")
    videos = scraper.search("machine learning", sort="view_count", limit=10)

    with open("youtube_results.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_FIELDS))
        writer.writeheader()
        for video in videos:
            writer.writerow(video.to_dict())

    print(f"Wrote {len(videos)} rows to youtube_results.csv")


if __name__ == "__main__":
    main()
