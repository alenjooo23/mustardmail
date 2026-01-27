# YouTube Creator Scraper

A Python tool that discovers business-focused YouTube creators (10K-500K subscribers) who are actively uploading in 2025 and don't have a Twitter/X presence. Results are ranked by engagement and exported to CSV for outreach.

## Features

- **Channel Discovery** - Searches YouTube using 10 business-related keywords
- **Subscriber Filtering** - Targets mid-tier creators (10,000-500,000 subscribers)
- **2025 Activity Filter** - Only includes creators who have uploaded at least one video in 2025 or later
- **Twitter/X Detection** - Excludes channels that list Twitter or X links in their description
- **Engagement Ranking** - Assigns A/B/C tiers based on subscriber count and average views
- **Deduplication** - Channels found across multiple keywords are only included once
- **CSV Export** - Clean output file with all relevant metrics

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your YouTube API key

Get an API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) with the YouTube Data API v3 enabled.

```bash
export YOUTUBE_API_KEY='your-api-key-here'
```

## Usage

```bash
python main.py
```

The script will:
1. Search for channels across all configured keywords
2. Filter by recent upload activity (2025+)
3. Remove channels with Twitter/X presence
4. Rank remaining channels by engagement
5. Export results to a CSV file

## Output Format

The script generates a file named `youtube_prospects_YYYY-MM-DD.csv` with these columns:

| Column | Description |
|--------|-------------|
| `tier` | Engagement tier (A, B, or C) |
| `channel_name` | YouTube channel name |
| `subscriber_count` | Number of subscribers |
| `video_count` | Total videos on the channel |
| `avg_views_per_video` | Total views divided by video count |
| `views_per_subscriber` | Total views divided by subscriber count |
| `last_upload_date` | Date of the most recent video (YYYY-MM-DD) |
| `channel_url` | Direct link to the channel |
| `search_keyword` | The keyword that surfaced this channel |

## Tier Ranking

| Tier | Criteria |
|------|----------|
| **A** | 100K+ subscribers AND 10K+ average views per video |
| **B** | 50K+ subscribers OR 5K+ average views per video |
| **C** | Everything else within the subscriber range |

## Customization

Edit the configuration section at the top of `main.py`:

```python
MIN_SUBSCRIBERS = 10000      # Minimum subscriber count
MAX_SUBSCRIBERS = 500000     # Maximum subscriber count
MIN_UPLOAD_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)  # Activity cutoff
MAX_RESULTS = 200            # Total channels to process
KEYWORDS = [...]             # Search terms to use
```

## Troubleshooting

**"YOUTUBE_API_KEY environment variable is not set"**
Set the environment variable before running: `export YOUTUBE_API_KEY='your-key'`

**API quota exceeded**
The YouTube Data API has a daily quota (typically 10,000 units). Reduce `MAX_RESULTS` or the number of keywords. Quota resets at midnight Pacific Time.

**No channels found**
Verify your API key is valid and has YouTube Data API v3 enabled in the Google Cloud Console.

**Empty CSV output**
This usually means all found channels were filtered out. Try relaxing the subscriber range or date filter in the configuration.
