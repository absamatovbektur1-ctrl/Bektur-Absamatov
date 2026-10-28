# Schedule Instagram Reels via Metricool API (Python)

A complete guide to programmatically scheduling Instagram Reels using the Metricool API and Python. Upload your video, set a time, and Metricool handles the publishing.

---

## Prerequisites

- A [Metricool](https://metricool.com) account with an Instagram profile connected
- Your Metricool **API token**, **user ID**, and **blog ID** (see [Finding Your Credentials](#finding-your-credentials))
- Python 3.8+
- The `requests` library (`pip install requests`)

Link to Metricool: https://i.mtr.cool/omnifusion (this is an affiliate link and supports the channel)

---

## How It Works

Metricool's scheduler API accepts a video URL (not a file upload). So the flow is:

1. **Upload** your video to a temporary file host (we use tmpfiles.org)
2. **Create a scheduled post** in Metricool with the video URL, caption, and publish time
3. **Metricool downloads the video**, re-hosts it, and publishes it at the scheduled time

---

## Step 1: Upload Your Video

Metricool expects a publicly accessible URL for the video. We use [tmpfiles.org](https://tmpfiles.org) as a free, no-auth temporary host. The file stays available long enough for Metricool to download it.

```python
import requests

def upload_to_tmpfiles(video_path):
    """Upload a video file to tmpfiles.org, return a direct download URL."""
    with open(video_path, "rb") as f:
        r = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": f},
            timeout=180,
        )

    if r.status_code == 200:
        # tmpfiles returns a page URL - convert to direct download link
        raw_url = r.json()["data"]["url"]
        return raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    else:
        raise Exception(f"Upload failed: {r.status_code}")
```

**Note:** tmpfiles.org links expire after ~60 minutes. That's fine - Metricool downloads and re-hosts the video immediately when you create the post. If you prefer, you can use any service that gives you a direct download URL (S3 presigned URL, your own server, etc.).

---

## Step 2: Schedule the Post

Once you have a video URL, create a scheduled post via the Metricool API.

```python
from datetime import datetime, timedelta

METRICOOL_API = "https://app.metricool.com/api"

def schedule_reel(video_url, caption, schedule_time, api_token, user_id, blog_id):
    """Schedule an Instagram Reel via Metricool API.

    Args:
        video_url: Direct download URL to the video file.
        caption: The post caption text.
        schedule_time: datetime object for when to publish.
        api_token: Your Metricool API token.
        user_id: Your Metricool user ID.
        blog_id: Your Metricool blog ID (Instagram profile).

    Returns:
        dict with post data including 'id'.
    """
    r = requests.post(
        f"{METRICOOL_API}/v2/scheduler/posts",
        headers={
            "X-Mc-Auth": api_token,
            "Content-Type": "application/json",
        },
        params={
            "userId": user_id,
            "blogId": blog_id,
        },
        json={
            "text": caption,
            "publicationDate": {
                "dateTime": schedule_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timezone": "America/New_York",  # Change to your timezone
            },
            "draft": False,
            "autoPublish": True,
            "saveExternalMediaFiles": True,
            "providers": [{"network": "INSTAGRAM"}],
            "instagramData": {
                "type": "TRIAL_REEL",
                "shareTrialAutomatically": False,
            },
            "media": [video_url],
        },
        timeout=30,
    )

    if r.status_code in [200, 201]:
        return r.json().get("data", {})
    else:
        raise Exception(f"Post failed ({r.status_code}): {r.text[:300]}")
```

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| `text` | Your caption. Supports line breaks and emojis. |
| `publicationDate.dateTime` | ISO 8601 format without timezone offset (e.g. `2025-03-20T14:00:00`) |
| `publicationDate.timezone` | IANA timezone string (e.g. `America/New_York`, `Europe/London`, `Asia/Tokyo`) |
| `autoPublish` | `True` to publish automatically; `False` to leave as draft |
| `instagramData.type` | `"TRIAL_REEL"` for Reels |
| `instagramData.shareTrialAutomatically` | `True` to also share the reel to your feed |
| `media` | Array of URLs. For a reel, this is a single video URL. |
| `saveExternalMediaFiles` | `True` so Metricool downloads and caches the video |

---

## Putting It Together

Here's a complete, minimal script that schedules a single reel:

```python
#!/usr/bin/env python3
"""Schedule a single Instagram Reel via Metricool."""

import requests
from datetime import datetime, timedelta

# ---- Configuration ----
API_TOKEN = "your_metricool_api_token"
USER_ID = "your_user_id"
BLOG_ID = "your_blog_id"
TIMEZONE = "America/New_York"

METRICOOL_API = "https://app.metricool.com/api"


def upload_to_tmpfiles(video_path):
    with open(video_path, "rb") as f:
        r = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": f},
            timeout=180,
        )
    if r.status_code == 200:
        raw_url = r.json()["data"]["url"]
        return raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    else:
        raise Exception(f"Upload failed: {r.status_code}")


def schedule_reel(video_url, caption, schedule_time):
    r = requests.post(
        f"{METRICOOL_API}/v2/scheduler/posts",
        headers={"X-Mc-Auth": API_TOKEN, "Content-Type": "application/json"},
        params={"userId": USER_ID, "blogId": BLOG_ID},
        json={
            "text": caption,
            "publicationDate": {
                "dateTime": schedule_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timezone": TIMEZONE,
            },
            "draft": False,
            "autoPublish": True,
            "saveExternalMediaFiles": True,
            "providers": [{"network": "INSTAGRAM"}],
            "instagramData": {
                "type": "TRIAL_REEL",
                "shareTrialAutomatically": False,
            },
            "media": [video_url],
        },
        timeout=30,
    )
    if r.status_code in [200, 201]:
        return r.json().get("data", {})
    else:
        raise Exception(f"Post failed ({r.status_code}): {r.text[:300]}")


# ---- Main ----
video_path = "my_reel.mp4"
caption = "Your caption here"
publish_time = datetime.now() + timedelta(hours=1)  # 1 hour from now

print(f"Uploading {video_path}...")
url = upload_to_tmpfiles(video_path)
print(f"Uploaded: {url}")

print(f"Scheduling for {publish_time.strftime('%Y-%m-%d %H:%M')}...")
result = schedule_reel(url, caption, publish_time)
print(f"Scheduled! Post ID: {result.get('id')}")
```

---

## Batch Scheduling

To schedule multiple reels with spacing between them:

```python
import time
from pathlib import Path

def schedule_batch(video_folder, captions, interval_minutes=20, start_delay_minutes=10):
    """Schedule all .mp4 files in a folder as reels.

    Args:
        video_folder: Path to folder containing .mp4 files.
        captions: List of caption strings (one per video, in order).
        interval_minutes: Minutes between each scheduled post.
        start_delay_minutes: Minutes from now to schedule the first post.
    """
    videos = sorted(Path(video_folder).glob("*.mp4"))
    schedule_time = datetime.now() + timedelta(minutes=start_delay_minutes)

    for idx, video_path in enumerate(videos):
        caption = captions[idx] if idx < len(captions) else f"Reel {idx + 1}"

        print(f"\n[{idx + 1}/{len(videos)}] {video_path.name}")
        print(f"  Caption: {caption[:60]}")
        print(f"  Scheduled: {schedule_time.strftime('%Y-%m-%d %H:%M')}")

        try:
            video_url = upload_to_tmpfiles(str(video_path))
            result = schedule_reel(video_url, caption, schedule_time)
            print(f"  OK (ID: {result.get('id')})")

            schedule_time += timedelta(minutes=interval_minutes)
            time.sleep(2)  # Small delay between API calls

        except Exception as e:
            print(f"  FAILED: {e}")

# Usage:
captions = [
    "Caption for reel 1",
    "Caption for reel 2",
    "Caption for reel 3",
]
schedule_batch("./my_reels/", captions, interval_minutes=30, start_delay_minutes=15)
```

**Tip:** Add a 2-second `time.sleep()` between posts to avoid rate limiting.

---

## Finding Your Credentials

### API Token
1. Log in to [Metricool](https://app.metricool.com)
2. Go to **Integrations** or **API** settings
3. Generate or copy your API token

### User ID and Blog ID
These are included in API responses and visible in network requests when using the Metricool web app. The easiest way:
1. Open the Metricool web app
2. Open your browser's Developer Tools (F12) -> Network tab
3. Navigate around the scheduler - look for API calls to `app.metricool.com/api`
4. Check the query parameters for `userId` and `blogId`

---

## Common `instagramData.type` Values

| Type | Description |
|------|-------------|
| `TRIAL_REEL` | Instagram Reel |
| `POST` | Image post or carousel |

For carousels, pass multiple image URLs in the `media` array.

---

## Error Handling Tips

- **401 Unauthorized** - Check your API token is correct and active
- **400 Bad Request** - Usually a malformed body (check timezone string, datetime format)
- **Video download fails** - Make sure the video URL is a direct download link, not a page URL
- **Rate limiting** - Add delays between batch requests (2+ seconds recommended)
- **Never retry blindly** - If a post fails, check the Metricool dashboard first. The post may have been created even if the response errored. Retrying could create duplicates.

---

## Full API Reference

**Endpoint:** `POST https://app.metricool.com/api/v2/scheduler/posts`

**Headers:**
```
X-Mc-Auth: {your_api_token}
Content-Type: application/json
```

**Query Parameters:**
```
userId={your_user_id}&blogId={your_blog_id}
```

**Body (JSON):**
```json
{
  "text": "Your caption",
  "publicationDate": {
    "dateTime": "2025-03-20T14:00:00",
    "timezone": "America/New_York"
  },
  "draft": false,
  "autoPublish": true,
  "saveExternalMediaFiles": true,
  "providers": [{"network": "INSTAGRAM"}],
  "instagramData": {
    "type": "TRIAL_REEL",
    "shareTrialAutomatically": false
  },
  "media": ["https://your-video-url.com/video.mp4"]
}
```

**Success Response:** `200` or `201` with `{ "data": { "id": "post_id", ... } }`
