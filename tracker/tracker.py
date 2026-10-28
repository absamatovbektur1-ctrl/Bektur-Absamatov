#!/usr/bin/env python3
"""
Instagram Post Tracker: snapshot your post stats from Metricool into tracker.db.

    python3 tracker/tracker.py

Run once a day; each run adds a snapshot so you can see growth over time.
Spec: docs/guides/instagram-post-tracker.md
"""

import json
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from envfile import require  # noqa: E402

API_BASE = "https://app.metricool.com/api/v2"
DB_PATH = HERE / "tracker.db"
LOOKBACK_DAYS = 90

USER_ID, BLOG_ID, API_TOKEN = require("METRICOOL_USER_ID", "METRICOOL_BLOG_ID", "METRICOOL_API_TOKEN")


def setup_db(conn):
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
    query = urllib.parse.urlencode({"userId": USER_ID, "blogId": BLOG_ID})
    sep = "&" if "?" in path else "?"
    req = urllib.request.Request(API_BASE + path + sep + query)
    req.add_header("X-Mc-Auth", API_TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit("Metricool вернул ошибку (HTTP %s).\n%s\nПроверь ключи в .env." % (exc.code, body))
    except urllib.error.URLError as exc:
        raise SystemExit("Не удалось достучаться до Metricool: %s" % exc.reason)
    if isinstance(payload, dict):
        return payload.get("data") or []
    return payload if isinstance(payload, list) else []


def pull_posts():
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
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for p in posts:
        conn.execute(
            "INSERT INTO content (post_id, permalink, post_type, caption, published_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(post_id) DO UPDATE SET "
            "permalink=excluded.permalink, caption=excluded.caption, published_at=excluded.published_at",
            (p["post_id"], p["permalink"], p["post_type"], p["caption"], p["published_at"]))
        conn.execute(
            "INSERT INTO metrics (post_id, checked_at, views, likes, comments, saves, shares, reach, engagement) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (p["post_id"], checked_at, p["views"], p["likes"], p["comments"],
             p["saves"], p["shares"], p["reach"], p["engagement"]))
    conn.commit()
    return checked_at


def show_report(conn):
    rows = conn.execute("""
        SELECT c.post_type, c.caption, m.views, m.likes, m.engagement
        FROM content c
        JOIN metrics m ON m.id = (
            SELECT id FROM metrics WHERE post_id = c.post_id ORDER BY checked_at DESC LIMIT 1
        )
        ORDER BY COALESCE(m.views, 0) DESC
        LIMIT 10
    """).fetchall()
    if not rows:
        print("\nПостов пока нет.\n")
        return
    print("\n  ТОП-10 ПОСТОВ ПО ПРОСМОТРАМ\n")
    for i, r in enumerate(rows, 1):
        caption = " ".join((r["caption"] or "").split())[:46]
        print("  %2d. [%-4s] %9s просм.  %7s лайков  %5.1f%%   %s" % (
            i, r["post_type"], "{:,}".format(r["views"] or 0), "{:,}".format(r["likes"] or 0),
            r["engagement"] or 0.0, caption))
    print()


def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        setup_db(conn)
        print("Загружаю посты из Metricool...")
        posts = pull_posts()
        checked_at = save_snapshot(conn, posts)
        print("Сохранено %d постов. Снимок: %s UTC." % (len(posts), checked_at))
        show_report(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
