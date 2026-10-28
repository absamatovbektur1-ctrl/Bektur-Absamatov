# Instagram Post Tracker

A free, no-frills way to see which of your Instagram posts actually perform. It
pulls your post stats out of Metricool into a small database on your own
computer, takes a fresh snapshot every time it runs, and lets you ask Claude
plain questions about what is working.

Two small files. No libraries to install.

## How to use this

Open Claude Code, or any Claude that can create files and run things on your
computer. Give it this whole file and say:

> Set this up for me.

Claude will create the files, connect your Metricool account, run it, and show
you your top posts. Everything below is written for Claude to follow and for you
to understand what it built.

## What it does

- Pulls every reel and feed post from your last 90 days out of Metricool.
- Saves them to a local database file, `tracker.db`.
- Each run takes a fresh snapshot, so post numbers build into a history. That
  history is the point: a single number cannot tell you whether a post is still
  climbing or already dead, but a week of snapshots can.
- Prints your top 10 posts by views.
- Lets you ask Claude anything about the data afterwards.

## What you need

- Python 3.9 or newer.
- A Metricool account on a paid plan (their API is a paid feature).
- Your Instagram account connected inside Metricool.
- Three Metricool credentials: user ID, blog ID, API token.

Link to Metricool: https://i.mtr.cool/omnifusion (this is an affiliate link and supports the channel)

## Where to find your Metricool credentials

All three belong to your own Metricool account:

- **API token and user ID** - Metricool's API comes with their paid plans. In
  Metricool, open your settings and find the API section. It shows your access
  token and your user ID. If you cannot find it, Metricool support will point
  you there.
- **Blog ID** - Metricool calls each connected account a "blog". Open your
  account in Metricool and look at the browser address bar: the URL contains
  `blogId=` (or `blog=`) followed by a number. That number is your blog ID.

---

## For Claude: set this up

Work through these steps for the person who gave you this file.

1. Create a folder for the tracker (suggest `post-tracker/`).
2. Create `config.py` and `tracker.py` inside it, exactly as written below.
3. Ask the user for their three Metricool credentials and paste them into
   `config.py`. Treat the API token as a password - do not print it back.
4. Run `python3 tracker.py`. If it fails with an authorization error, a
   credential is wrong - fix it and retry. The first run can take a moment.
5. Show them the report it printed.
6. Set up the daily run (see "Run it every day" below) for their operating
   system.
7. Tell them they can now ask you questions about their posts, and that the
   history gets more useful every day the tracker runs.

## The files

### `config.py`

```python
# config.py
# Your Metricool credentials. Paste each value between the quotes, then save.
# Keep this file private - the API token is a password.

METRICOOL_USER_ID   = "paste your user id here"
METRICOOL_BLOG_ID   = "paste your blog id here"
METRICOOL_API_TOKEN = "paste your api token here"
```

### `tracker.py`

```python
"""
Instagram Post Tracker - a free starter kit.

Pulls your Instagram post stats from Metricool into a local database, so you
can see which posts performed best and ask Claude about them. Run it once a
day and it builds a history over time.

    python3 tracker.py
"""
import json
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import config
except ImportError:
    raise SystemExit(
        "config.py not found. Create it next to tracker.py with your three "
        "Metricool credentials - see the guide.")

API_BASE = "https://app.metricool.com/api/v2"
DB_PATH = Path(__file__).resolve().parent / "tracker.db"
LOOKBACK_DAYS = 90


def setup_db(conn):
    """Create the two tables if they do not exist yet."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS content (
            post_id       TEXT PRIMARY KEY,
            permalink     TEXT,
            post_type     TEXT,
            caption       TEXT,
            published_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id     TEXT NOT NULL,
            checked_at  TEXT NOT NULL,
            views       INTEGER,
            likes       INTEGER,
            comments    INTEGER,
            saves       INTEGER,
            shares      INTEGER,
            reach       INTEGER,
            engagement  REAL
        );
    """)
    conn.commit()


def metricool_get(path):
    """Call a Metricool API endpoint and return its list of results."""
    query = urllib.parse.urlencode({
        "userId": config.METRICOOL_USER_ID,
        "blogId": config.METRICOOL_BLOG_ID,
    })
    sep = "&" if "?" in path else "?"
    req = urllib.request.Request(API_BASE + path + sep + query)
    req.add_header("X-Mc-Auth", config.METRICOOL_API_TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(
            "Metricool returned an error (HTTP %s).\n%s\n"
            "Check the three values in config.py." % (exc.code, body))
    except urllib.error.URLError as exc:
        raise SystemExit("Could not reach Metricool: %s" % exc.reason)
    if isinstance(payload, dict):
        return payload.get("data") or []
    return payload if isinstance(payload, list) else []


def pull_posts():
    """Pull reels and feed posts from the last LOOKBACK_DAYS."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=LOOKBACK_DAYS)
    window = urllib.parse.urlencode({
        "from": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    endpoints = (
        ("reel", "/analytics/reels/instagram"),
        ("post", "/analytics/posts/instagram"),
    )
    posts = []
    for post_type, endpoint in endpoints:
        for raw in metricool_get(endpoint + "?" + window):
            post_id = raw.get("reelId") or raw.get("postId") or raw.get("id")
            if not post_id:
                continue
            published = raw.get("publishedAt")
            if isinstance(published, dict):
                published = published.get("dateTime")
            saves = raw.get("saves")
            if saves is None:
                saves = raw.get("saved")
            posts.append({
                "post_id": str(post_id),
                "permalink": raw.get("url"),
                "post_type": post_type,
                "caption": raw.get("content"),
                "published_at": published,
                "views": raw.get("views"),
                "likes": raw.get("likes"),
                "comments": raw.get("comments"),
                "saves": saves,
                "shares": raw.get("shares"),
                "reach": raw.get("reach"),
                "engagement": raw.get("engagement"),
            })
    return posts


def save_snapshot(conn, posts):
    """Store each post and a fresh metrics snapshot."""
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for p in posts:
        conn.execute(
            "INSERT INTO content (post_id, permalink, post_type, caption, "
            "published_at) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(post_id) DO UPDATE SET "
            "permalink=excluded.permalink, caption=excluded.caption, "
            "published_at=excluded.published_at",
            (p["post_id"], p["permalink"], p["post_type"], p["caption"],
             p["published_at"]))
        conn.execute(
            "INSERT INTO metrics (post_id, checked_at, views, likes, comments, "
            "saves, shares, reach, engagement) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (p["post_id"], checked_at, p["views"], p["likes"], p["comments"],
             p["saves"], p["shares"], p["reach"], p["engagement"]))
    conn.commit()
    return checked_at


def show_report(conn):
    """Print the top 10 posts by views, using the latest snapshot of each."""
    rows = conn.execute("""
        SELECT c.post_type, c.caption, m.views, m.likes, m.engagement
        FROM content c
        JOIN metrics m ON m.id = (
            SELECT id FROM metrics
            WHERE post_id = c.post_id
            ORDER BY checked_at DESC
            LIMIT 1
        )
        ORDER BY COALESCE(m.views, 0) DESC
        LIMIT 10
    """).fetchall()
    if not rows:
        print("\nNo posts found yet.\n")
        return
    print("\n  YOUR TOP 10 POSTS BY VIEWS\n")
    for i, r in enumerate(rows, 1):
        caption = " ".join((r["caption"] or "").split())[:46]
        print("  %2d. [%-4s] %9s views   %7s likes   %5.1f%%   %s" % (
            i, r["post_type"],
            "{:,}".format(r["views"] or 0),
            "{:,}".format(r["likes"] or 0),
            r["engagement"] or 0.0,
            caption))
    print()


def main():
    for name in ("METRICOOL_USER_ID", "METRICOOL_BLOG_ID", "METRICOOL_API_TOKEN"):
        value = getattr(config, name, "")
        if not value or "paste" in str(value).lower():
            raise SystemExit("Add your %s to config.py first." % name)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        setup_db(conn)
        print("Fetching your posts from Metricool ...")
        posts = pull_posts()
        checked_at = save_snapshot(conn, posts)
        print("Saved %d posts. Snapshot taken at %s UTC." % (len(posts), checked_at))
        show_report(conn)
        print("Run this again tomorrow to keep building your history.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

Keep `config.py` and `tracker.db` private - they hold your token and your data.
If you put this folder in a git repo, ignore both.

## Run it every day

The tracker is worth running once a day. Each run adds a snapshot, and the
history is what lets you see whether a post kept climbing after day one.

On macOS or Linux, run `crontab -e` and add this line (use the real full path to
your folder):

```
0 20 * * * cd /full/path/to/post-tracker && python3 tracker.py >> tracker.log 2>&1
```

That runs it every day at 8pm. On Windows, ask Claude to set up a daily
scheduled task. Or just run `python3 tracker.py` yourself whenever you remember.

## Ask Claude about your posts

This is the payoff. After the tracker has run a few times, open Claude in the
folder and ask in plain English. Claude reads `tracker.db` directly.

- "Which of my posts got the most views in the last month?"
- "Do my reels or my feed posts get more engagement on average?"
- "Show me how this post's views grew day by day since I posted it: [paste a URL]"
- "Which posts get saved the most relative to their views?"
- "Find the posts that did worse than my recent average."

The database has two tables. `content` has one row per post. `metrics` has one
row per post per time the tracker ran, so a post you have tracked for a week has
seven rows - that is your growth history.

## If something breaks

- **HTTP 401 or 403:** a credential is wrong. Re-check the three values in
  `config.py`. The blog ID must be the account you connected Instagram to.
- **No posts found:** the account has no reels or feed posts in the last 90
  days, or Metricool's data for very recent posts lags a few hours.
- **"No module named config":** `config.py` must sit in the same folder as
  `tracker.py`.

---

This is yours to use, change, and share.
