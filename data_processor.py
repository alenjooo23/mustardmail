"""Data filtering, ranking, and CSV export for YouTube channel data."""

import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def calculate_metrics(channel):
    """Calculate engagement metrics for a channel.

    Args:
        channel: Channel dictionary with total_views, video_count, subscriber_count.

    Returns:
        Channel dictionary with added avg_views_per_video and views_per_subscriber.
    """
    video_count = channel.get('video_count', 0)
    total_views = channel.get('total_views', 0)
    subscriber_count = channel.get('subscriber_count', 0)

    if video_count > 0:
        channel['avg_views_per_video'] = total_views / video_count
    else:
        channel['avg_views_per_video'] = 0

    if subscriber_count > 0:
        channel['views_per_subscriber'] = total_views / subscriber_count
    else:
        channel['views_per_subscriber'] = 0

    return channel


def assign_tier(channel):
    """Assign a ranking tier to a channel based on engagement.

    Tier A: 100K+ subscribers AND 10K+ avg views per video
    Tier B: 50K+ subscribers OR 5K+ avg views per video
    Tier C: Everything else

    Args:
        channel: Channel dictionary with subscriber_count and avg_views_per_video.

    Returns:
        Tier string: 'A', 'B', or 'C'.
    """
    subs = channel.get('subscriber_count', 0)
    avg_views = channel.get('avg_views_per_video', 0)

    if subs >= 100000 and avg_views >= 10000:
        return 'A'
    elif subs >= 50000 or avg_views >= 5000:
        return 'B'
    else:
        return 'C'


def rank_channels(channels):
    """Calculate metrics and assign tiers for all channels.

    Args:
        channels: List of channel dictionaries.

    Returns:
        List of channels with metrics calculated and tiers assigned,
        sorted by tier (A first) then by subscriber count descending.
    """
    for channel in channels:
        calculate_metrics(channel)
        channel['tier'] = assign_tier(channel)

    tier_order = {'A': 0, 'B': 1, 'C': 2}
    channels.sort(key=lambda ch: (tier_order.get(ch['tier'], 3),
                                  -ch['subscriber_count']))

    tier_counts = {}
    for ch in channels:
        tier_counts[ch['tier']] = tier_counts.get(ch['tier'], 0) + 1

    for tier in ['A', 'B', 'C']:
        logger.info("Tier %s: %d channels", tier, tier_counts.get(tier, 0))

    return channels


def export_to_csv(channels, filename=None):
    """Export ranked channels to a CSV file.

    Args:
        channels: List of ranked channel dictionaries.
        filename: Output filename. Defaults to youtube_prospects_YYYY-MM-DD.csv.

    Returns:
        The filename that was written to.
    """
    if filename is None:
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"youtube_prospects_{today}.csv"

    fieldnames = [
        'tier',
        'channel_name',
        'subscriber_count',
        'video_count',
        'avg_views_per_video',
        'views_per_subscriber',
        'last_upload_date',
        'channel_url',
        'search_keyword',
    ]

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                    extrasaction='ignore')
            writer.writeheader()

            for channel in channels:
                row = {
                    'tier': channel.get('tier', 'C'),
                    'channel_name': channel.get('channel_name', ''),
                    'subscriber_count': channel.get('subscriber_count', 0),
                    'video_count': channel.get('video_count', 0),
                    'avg_views_per_video': round(channel.get('avg_views_per_video', 0), 2),
                    'views_per_subscriber': round(channel.get('views_per_subscriber', 0), 2),
                    'last_upload_date': channel.get('last_upload_date', ''),
                    'channel_url': channel.get('channel_url', ''),
                    'search_keyword': channel.get('search_keyword', ''),
                }
                writer.writerow(row)

        logger.info("Exported %d channels to %s", len(channels), filename)
        return filename

    except IOError as e:
        logger.error("Failed to write CSV file %s: %s", filename, e)
        raise
