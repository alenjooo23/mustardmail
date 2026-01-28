"""Main execution script for the YouTube Creator Scraper."""

import logging
import os
import sys
from datetime import datetime, timezone

from youtube_scraper import YouTubeScraper
from data_processor import rank_channels, export_to_csv

# ── Configuration ─────────────────────────────────────────────────────────────
MIN_SUBSCRIBERS = 10000
MAX_SUBSCRIBERS = 500000
MIN_UPLOAD_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
MAX_RESULTS = 500  # Total channels to process across all keywords
ALLOWED_COUNTRIES = ['US', 'CA', 'GB']  # United States, Canada, United Kingdom

KEYWORDS = [
    "business tips",
    "entrepreneurship",
    "startup advice",
    "small business",
    "business coaching",
    "digital marketing",
    "online business",
    "business strategy",
    "sales training",
    "solopreneur",
]

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def print_config():
    """Print the current configuration summary."""
    print("\n" + "=" * 60)
    print("  YouTube Creator Scraper")
    print("=" * 60)
    print(f"\n  Subscriber range : {MIN_SUBSCRIBERS:,} - {MAX_SUBSCRIBERS:,}")
    print(f"  Minimum upload   : {MIN_UPLOAD_DATE.strftime('%Y-%m-%d')}")
    print(f"  Keywords         : {len(KEYWORDS)}")
    print(f"  Max channels     : {MAX_RESULTS}")
    print("=" * 60 + "\n")


def main():
    # ── Validate API Key ──────────────────────────────────────────────────────
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("ERROR: YOUTUBE_API_KEY environment variable is not set.")
        print("\nTo set it:")
        print("  export YOUTUBE_API_KEY='your-api-key-here'")
        print("\nGet an API key at: https://console.cloud.google.com/apis/credentials")
        sys.exit(1)

    print_config()

    scraper = YouTubeScraper(api_key)

    # ── Step 1: Search for Channels ───────────────────────────────────────────
    print("[Step 1/6] Searching for channels...")
    all_channel_ids = set()  # Use set for deduplication
    keyword_map = {}  # Track which keyword found each channel

    for keyword in KEYWORDS:
        results_per_keyword = max(1, MAX_RESULTS // len(KEYWORDS))
        channel_ids = scraper.search_channels(keyword, max_results=results_per_keyword)
        for cid in channel_ids:
            if cid not in all_channel_ids:
                keyword_map[cid] = keyword
            all_channel_ids.add(cid)

        if len(all_channel_ids) >= MAX_RESULTS:
            break

    unique_ids = list(all_channel_ids)[:MAX_RESULTS]
    print(f"  Found {len(unique_ids)} unique channels across {len(KEYWORDS)} keywords\n")

    if not unique_ids:
        print("No channels found. Check your API key and quota.")
        sys.exit(0)

    # Fetch full channel details
    print("  Fetching channel details...")
    channels = scraper.get_channel_details(unique_ids)

    # Attach the search keyword to each channel
    for channel in channels:
        channel['search_keyword'] = keyword_map.get(channel['channel_id'], '')

    # Filter by subscriber count
    channels = scraper.filter_by_subscribers(channels, MIN_SUBSCRIBERS, MAX_SUBSCRIBERS)
    print(f"  Channels in subscriber range: {len(channels)}\n")

    if not channels:
        print("No channels match the subscriber criteria.")
        sys.exit(0)

    # ── Step 2: Filter by Country ─────────────────────────────────────────────
    print("[Step 2/6] Filtering by country (US, CA, UK)...")
    channels = scraper.filter_by_country(channels, ALLOWED_COUNTRIES)
    print(f"  Channels in allowed countries: {len(channels)}\n")

    if not channels:
        print("No channels match the country criteria.")
        sys.exit(0)

    # ── Step 3: Filter by Recent Activity ─────────────────────────────────────
    print("[Step 3/6] Checking upload activity (2025+)...")
    channels = scraper.filter_by_activity(channels, MIN_UPLOAD_DATE)
    print(f"  Active channels (uploaded since {MIN_UPLOAD_DATE.strftime('%Y-%m-%d')}): {len(channels)}\n")

    if not channels:
        print("No channels have recent uploads matching the date filter.")
        sys.exit(0)

    # ── Step 4: Filter by No Twitter ──────────────────────────────────────────
    print("[Step 4/6] Filtering out channels with Twitter/X presence...")
    channels = scraper.filter_by_no_twitter(channels)
    print(f"  Channels without Twitter/X: {len(channels)}\n")

    if not channels:
        print("All remaining channels have Twitter/X presence.")
        sys.exit(0)

    # ── Step 5: Rank Channels ─────────────────────────────────────────────────
    print("[Step 5/6] Ranking channels by engagement...")
    channels = rank_channels(channels)

    tier_counts = {'A': 0, 'B': 0, 'C': 0}
    for ch in channels:
        tier_counts[ch['tier']] = tier_counts.get(ch['tier'], 0) + 1

    print(f"  Tier A (top performers) : {tier_counts['A']}")
    print(f"  Tier B (solid channels) : {tier_counts['B']}")
    print(f"  Tier C (emerging)       : {tier_counts['C']}\n")

    # ── Step 6: Export to CSV ─────────────────────────────────────────────────
    print("[Step 6/6] Exporting results to CSV...")
    filename = export_to_csv(channels)
    print(f"  Saved to: {filename}\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("=" * 60)
    print("  COMPLETE")
    print("=" * 60)
    print(f"  Total prospects : {len(channels)}")
    print(f"  Output file     : {filename}")
    print("=" * 60)

    print("\n  Next steps:")
    print("  1. Open the CSV file to review prospects")
    print("  2. Start with Tier A channels for highest impact")
    print("  3. Verify channel details before outreach")
    print()


if __name__ == '__main__':
    main()
