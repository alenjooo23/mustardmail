"""YouTube API interactions for channel discovery and data collection."""

import logging
import re
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

TWITTER_PATTERNS = [
    r'twitter\.com/',
    r'x\.com/',
    r'@\w+',
]


class YouTubeScraper:
    """Handles YouTube Data API v3 interactions."""

    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def search_channels(self, keyword, max_results=50):
        """Search for YouTube channels by keyword.

        Args:
            keyword: Search term to find channels.
            max_results: Maximum number of results to return.

        Returns:
            List of channel IDs found for the keyword.
        """
        channel_ids = []
        next_page_token = None

        while len(channel_ids) < max_results:
            try:
                request = self.youtube.search().list(
                    part='snippet',
                    q=keyword,
                    type='channel',
                    maxResults=min(50, max_results - len(channel_ids)),
                    pageToken=next_page_token,
                )
                response = request.execute()

                for item in response.get('items', []):
                    channel_ids.append(item['snippet']['channelId'])

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            except HttpError as e:
                logger.error("API error searching for '%s': %s", keyword, e)
                break

        logger.info("Found %d channels for keyword '%s'", len(channel_ids), keyword)
        return channel_ids

    def get_channel_details(self, channel_ids):
        """Get detailed information for a list of channel IDs.

        Args:
            channel_ids: List of YouTube channel IDs.

        Returns:
            List of channel detail dictionaries.
        """
        channels = []

        # Process in batches of 50 (API limit)
        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i:i + 50]
            try:
                response = self.youtube.channels().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(batch),
                ).execute()

                for item in response.get('items', []):
                    stats = item.get('statistics', {})
                    snippet = item.get('snippet', {})
                    content_details = item.get('contentDetails', {})

                    subscriber_count = int(stats.get('subscriberCount', 0))
                    video_count = int(stats.get('videoCount', 0))
                    view_count = int(stats.get('viewCount', 0))

                    uploads_playlist_id = (
                        content_details
                        .get('relatedPlaylists', {})
                        .get('uploads', '')
                    )

                    channel_data = {
                        'channel_id': item['id'],
                        'channel_name': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'subscriber_count': subscriber_count,
                        'video_count': video_count,
                        'total_views': view_count,
                        'uploads_playlist_id': uploads_playlist_id,
                        'channel_url': f"https://www.youtube.com/channel/{item['id']}",
                    }
                    channels.append(channel_data)

            except HttpError as e:
                logger.error("API error fetching channel details: %s", e)

        return channels

    def get_latest_upload_date(self, uploads_playlist_id):
        """Get the publish date of the most recent video in a playlist.

        IMPORTANT: Do NOT use 'order' parameter in playlistItems().list()
        as it is not supported and will cause errors.

        Args:
            uploads_playlist_id: The uploads playlist ID for a channel.

        Returns:
            datetime object of the latest upload, or None if unavailable.
        """
        if not uploads_playlist_id:
            logger.warning("No uploads playlist ID provided")
            return None

        try:
            # DO NOT use 'order' parameter - it's not supported
            playlist_response = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=1,  # Gets most recent by default
            ).execute()

            items = playlist_response.get('items', [])
            if not items:
                logger.warning("No videos found in playlist %s", uploads_playlist_id)
                return None

            published_at = items[0]['contentDetails'].get('videoPublishedAt')
            if not published_at:
                logger.warning("No publish date for latest video in playlist %s",
                               uploads_playlist_id)
                return None

            # Properly handle timezone-aware datetime
            upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            return upload_date

        except HttpError as e:
            logger.error("API error fetching playlist %s: %s", uploads_playlist_id, e)
            return None

    @staticmethod
    def has_twitter_presence(description):
        """Check if a channel description contains Twitter/X links.

        Args:
            description: Channel description text.

        Returns:
            True if Twitter/X presence is detected, False otherwise.
        """
        if not description:
            return False

        description_lower = description.lower()
        for pattern in TWITTER_PATTERNS:
            if re.search(pattern, description_lower):
                return True
        return False

    def filter_by_subscribers(self, channels, min_subs, max_subs):
        """Filter channels by subscriber count range.

        Args:
            channels: List of channel dictionaries.
            min_subs: Minimum subscriber count (inclusive).
            max_subs: Maximum subscriber count (inclusive).

        Returns:
            List of channels within the subscriber range.
        """
        filtered = [
            ch for ch in channels
            if min_subs <= ch['subscriber_count'] <= max_subs
        ]
        logger.info("Filtered by subscribers (%d-%d): %d of %d channels",
                     min_subs, max_subs, len(filtered), len(channels))
        return filtered

    def filter_by_activity(self, channels, min_date):
        """Filter channels by most recent upload date.

        Both min_date and upload dates must be timezone-aware (UTC).

        Args:
            channels: List of channel dictionaries.
            min_date: Minimum upload date (timezone-aware datetime).

        Returns:
            List of channels with uploads on or after min_date.
        """
        active_channels = []
        for channel in channels:
            upload_date = self.get_latest_upload_date(
                channel.get('uploads_playlist_id', '')
            )
            if upload_date is None:
                logger.warning("Skipping channel '%s' - no upload date available",
                               channel.get('channel_name', 'Unknown'))
                continue

            if upload_date >= min_date:
                channel['last_upload_date'] = upload_date.strftime('%Y-%m-%d')
                active_channels.append(channel)
            else:
                logger.info("Channel '%s' last upload %s is before %s",
                            channel.get('channel_name', 'Unknown'),
                            upload_date.strftime('%Y-%m-%d'),
                            min_date.strftime('%Y-%m-%d'))

        logger.info("Filtered by activity (since %s): %d of %d channels",
                     min_date.strftime('%Y-%m-%d'), len(active_channels), len(channels))
        return active_channels

    def filter_by_no_twitter(self, channels):
        """Remove channels that have Twitter/X presence in their description.

        Args:
            channels: List of channel dictionaries.

        Returns:
            List of channels without Twitter/X presence.
        """
        filtered = [
            ch for ch in channels
            if not self.has_twitter_presence(ch.get('description', ''))
        ]
        logger.info("Filtered by no Twitter: %d of %d channels",
                     len(filtered), len(channels))
        return filtered
