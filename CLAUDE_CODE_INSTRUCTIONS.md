# YouTube Creator Scraper Project - Instructions for Claude Code

## Project Overview
Build a Python-based YouTube scraper that finds business content creators (10K-500K subscribers) who:
1. Do NOT have Twitter/X presence in their channel description
2. Have uploaded at least one video in 2025 or later (active creators only)
3. Are ranked by engagement metrics (A/B/C tiers)

## Technical Requirements

### Environment Setup
- Python 3.8+
- Virtual environment (venv)
- YouTube Data API v3 access
- Dependencies: google-api-python-client, google-auth

### Project Structure
```
youtube-scraper/
├── main.py                 # Main execution script
├── youtube_scraper.py      # YouTube API interactions
├── data_processor.py       # Data filtering and export
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
└── .gitignore             # Git ignore file
```

## Core Functionality

### 1. YouTube Search & Data Collection
- Search YouTube for channels using business-related keywords
- Keywords: ["business tips", "entrepreneurship", "startup advice", "small business", "business coaching", "digital marketing", "online business", "business strategy", "sales training", "solopreneur"]
- Filter by subscriber count: 10,000 - 500,000 subscribers
- Collect channel metadata: name, subscribers, video count, views, description, channel URL

### 2. Twitter Presence Detection
Check if channels have Twitter/X links in:
- Channel description (look for patterns: twitter.com/, x.com/, @username)
- EXCLUDE channels that have Twitter presence

### 3. Activity Filter (2025+ Uploads)
- For each channel, get the uploads playlist ID
- Fetch the most recent video from that playlist
- Parse the video's publish date
- ONLY include channels with videos published on or after January 1, 2025
- Handle timezone-aware datetime comparisons properly (use UTC)

### 4. Ranking System
Rank channels into tiers based on engagement:
- **Tier A**: 100K+ subscribers AND 10K+ avg views per video
- **Tier B**: 50K+ subscribers OR 5K+ avg views per video  
- **Tier C**: Everything else

Calculate metrics:
- Average views per video = total views / video count
- Views per subscriber ratio

### 5. CSV Export
Export filtered and ranked channels to CSV with columns:
- tier (A/B/C)
- channel_name
- subscriber_count
- video_count
- avg_views_per_video
- views_per_subscriber
- last_upload_date (YYYY-MM-DD format)
- channel_url
- search_keyword

Filename format: `youtube_prospects_YYYY-MM-DD.csv`

## Critical Implementation Details

### YouTube API Configuration
- API key should be stored as environment variable: `YOUTUBE_API_KEY`
- Handle API quota limits gracefully
- Proper error handling for HttpError exceptions

### Datetime Handling (IMPORTANT!)
- YouTube API returns timezone-aware datetimes (ISO 8601 format with 'Z')
- When comparing dates, ensure both datetimes are timezone-aware
- Use `datetime.timezone.utc` for min_date comparison
- Convert ISO format properly: `datetime.fromisoformat(published_at.replace('Z', '+00:00'))`

### YouTube API Calls
**DO NOT use 'order' parameter in playlistItems().list()** - it's not supported and will cause errors

Correct implementation:
```python
playlist_response = self.youtube.playlistItems().list(
    part='contentDetails',
    playlistId=uploads_playlist_id,
    maxResults=1  # Gets most recent by default
).execute()
```

### Logging
- Use Python's logging module
- Log levels: INFO for progress, WARNING for missing data, ERROR for failures
- Log key metrics: total channels found, filtered counts, export success

## User Experience

### Console Output Should Show:
1. Configuration summary (subscriber range, date filter, keywords)
2. Step-by-step progress (5 steps: Search → Filter by Date → Filter by Twitter → Rank → Export)
3. Statistics at each step (counts)
4. Final summary with output filename
5. Next steps guidance for the user

### Error Handling
- Graceful handling of missing API key
- API quota exceeded messages
- Missing upload dates (skip channel, log warning)
- Network errors (retry logic optional)

## Configuration Parameters
Make these easily configurable in main.py:
- `MIN_SUBSCRIBERS = 10000`
- `MAX_SUBSCRIBERS = 500000`
- `MIN_UPLOAD_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)`
- `KEYWORDS = [list of search terms]`
- `MAX_RESULTS = 200` (total channels to process)

## README.md Should Include
- Project description
- Features list (with emphasis on 2025 filter)
- Setup instructions (venv, pip install, API key setup)
- Usage instructions
- Output format explanation
- Tier ranking explanation
- Customization options
- Troubleshooting section

## .gitignore Should Include
```
venv/
*.pyc
__pycache__/
*.csv
.env
.DS_Store
```

## Testing Considerations
- Test with a small keyword set first (2-3 keywords)
- Verify timezone handling works correctly
- Ensure CSV exports properly with UTF-8 encoding
- Test with channels that have/don't have Twitter links
- Test with channels that have recent/old uploads

## Common Pitfalls to Avoid
1. ❌ Using 'order' parameter in playlistItems().list()
2. ❌ Comparing timezone-naive and timezone-aware datetimes
3. ❌ Not handling missing upload dates gracefully
4. ❌ Not using UTF-8 encoding for CSV export
5. ❌ Not deduplicating channels found across multiple keywords

## Success Criteria
- Script runs without errors
- Properly filters out channels with Twitter presence
- Correctly identifies active creators (2025+ uploads)
- Exports clean CSV with all required columns
- Provides clear console feedback throughout execution
- Code is modular and maintainable

## Current Status Note
This is a fresh rebuild. Previous versions had bugs with:
- Invalid 'order' parameter in YouTube API calls
- Timezone-naive vs timezone-aware datetime comparisons

These issues should be fixed from the start in this implementation.
