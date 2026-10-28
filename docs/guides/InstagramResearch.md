# Instagram Competitor Research Pipeline for Claude Code

A complete system that lets Claude Code scrape your Instagram competitors' reels, score them by virality and engagement, analyze hooks/themes/patterns, and generate a ranked report with content ideas - all from a single slash command.

**What it does:**
1. Scrapes recent reels from your tracked competitors via API
2. Scores each reel on virality, engagement, save rate, and recency
3. Analyzes captions for hook patterns, themes, and content formats
4. Generates a ranked markdown + JSON report
5. Claude interprets the data and suggests content ideas tailored to your niche

---

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and working
- Python 3.10+
- A data scraping API for Instagram (this pipeline uses [DataPrism](https://dataprism.dev) as primary, [Apify](https://apify.com) as fallback - you can swap in any Instagram scraping API)
- `requests` Python package (`pip install requests`)

Link to DataPrism: https://dataprism.dev/discount/emil (this is an affiliate link and supports the channel)

Link to Apify: https://www.apify.com?fpr=omnifusion (this is an affiliate link and supports the channel)

Link to HikerAPI, another Instagram scraping API you can swap in: https://hikerapi.com/p/a78naf3m (this is an affiliate link and supports the channel)

---

## Setup

### 1. Create the folder structure

From your Claude Code project root:

```
your-project/
├── .claude/commands/
│   └── instagram-research.md    # The slash command (Step 2)
├── .env                          # Your API keys (Step 3)
└── research/                     # The pipeline code (Step 4)
    ├── instagram_cli.py
    ├── competitors.json
    ├── data/
    │   └── config.json
    ├── instagram/
    │   ├── __init__.py
    │   ├── scraper.py
    │   ├── scorer.py
    │   └── analyzer.py
    ├── pipeline/
    │   ├── __init__.py
    │   ├── base.py
    │   └── instagram_research.py
    ├── output/
    │   ├── __init__.py
    │   └── reporter.py
    ├── cache/
    │   ├── __init__.py
    │   └── store.py
    └── reports/                  # Generated reports land here
```

### 2. Create the slash command

Save this as `.claude/commands/instagram-research.md`:

```markdown
# Instagram Competitor Research

Research what's performing on Instagram from tracked competitors. Scrape reels, score by engagement, analyze hooks/themes, and generate content ideas. Request: $ARGUMENTS

---

## Critical Rules

1. **No approval gates for intermediate steps.** Run the pipeline, present results. Only pause before final content plan output.
2. **Load .env before API calls.** `set -a; source "$CLAUDE_PROJECT_DIR/.env" 2>/dev/null; set +a`

---

## Commands

Parse `$ARGUMENTS` to determine the action:

- **`(empty or "run")`** - Run full research pipeline and present findings with content ideas
- **`add <username> <followers> [notes]`** - Add a competitor to track
- **`remove <username>`** - Remove a competitor
- **`list`** - Show tracked competitors
- **`report`** - Show latest research report

If no arguments or just `/instagram-research`, run the full pipeline.

---

## Working Directory

```bash
cd "$CLAUDE_PROJECT_DIR/research"
```

---

## Full Research Flow (default)

### Step 1: Run the Pipeline

```bash
cd "$CLAUDE_PROJECT_DIR/research"
set -a; source "$CLAUDE_PROJECT_DIR/.env" 2>/dev/null; set +a
python3 instagram_cli.py research --reels-per 30 --top 15
```

### Step 2: Read the Report

```bash
python3 instagram_cli.py report --latest --format markdown
```

### Step 3: Present Findings

Present a structured analysis:

- **Top Performing Reels** - Table: account, hook, likes, virality ratio, engagement rate, theme
- **Hook Patterns** - What opening patterns appear in top performers (Tool Reveal, Result/Proof, Contrarian, Listicle, etc.)
- **Theme Breakdown** - Which content themes drive the most engagement
- **Caption Analysis** - CTA usage, caption length trends, hashtag patterns

### Step 4: Generate Content Ideas

Based on the research findings, generate 10 content ideas for the user's brand:

For each idea:
- **Hook** (first line of caption)
- **Theme** (mapped to a top-performing theme)
- **Hook Pattern** (which pattern to use)
- **Why** (which competitor reel inspired it + what makes this angle unique)
- **Format suggestion** (talking head, screen recording, voiceover + B-roll)

Rank ideas by estimated potential based on:
1. Theme performance scores from the research
2. Hook pattern performance
3. Relevance to the user's niche
4. Content gap (things competitors cover that the user hasn't)

Present the ranked list.

---

## Competitor Management

### Add

```bash
cd "$CLAUDE_PROJECT_DIR/research"
python3 instagram_cli.py competitors --add <username> --followers <count> --notes "<notes>"
```

### Remove

```bash
python3 instagram_cli.py competitors --remove <username>
```

### List

```bash
python3 instagram_cli.py competitors --list
```

---

## Report Viewing

```bash
cd "$CLAUDE_PROJECT_DIR/research"
python3 instagram_cli.py report --latest --format markdown
# or JSON:
python3 instagram_cli.py report --latest --format json
# or specific date:
python3 instagram_cli.py report --date 2026-03-19
```
```

### 3. Set up your `.env`

Add your scraping API keys to your project's `.env` file:

```bash
# Primary scraping API (DataPrism)
DATAPRISM_API_KEY=your_key_here

# Fallback scraping API (Apify) - optional
APIFY_TOKEN=your_token_here
```

> **Note:** The scraper tries DataPrism first and falls back to Apify. You only need one. If you use a different Instagram scraping API, you'll modify `scraper.py` to match (see Step 4).

Link to DataPrism: https://dataprism.dev/discount/emil (this is an affiliate link and supports the channel)

Link to Apify: https://www.apify.com?fpr=omnifusion (this is an affiliate link and supports the channel)

### 4. Create the pipeline code

All `__init__.py` files are empty - just create blank files.

---

## Pipeline Code

### `research/instagram_cli.py`

The CLI entry point. Handles all subcommands (research, competitors, report, cache).

```python
#!/usr/bin/env python3
"""
Instagram Competitor Research CLI - find top-performing reels and extract content patterns.

Usage:
    python3 instagram_cli.py research                          # Full pipeline
    python3 instagram_cli.py research --reels-per 50 --top 20  # Custom limits
    python3 instagram_cli.py research --dry-run                # Preview only

    python3 instagram_cli.py competitors --list
    python3 instagram_cli.py competitors --add some_creator --followers 500000 --notes "AI tools"
    python3 instagram_cli.py competitors --remove some_creator

    python3 instagram_cli.py report --latest
    python3 instagram_cli.py report --date 2026-03-19
    python3 instagram_cli.py report --format json

    python3 instagram_cli.py cache --stats
    python3 instagram_cli.py cache --clear
"""

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def cmd_research(args):
    """Run Instagram competitor research pipeline."""
    from cache.store import CacheStore
    from instagram.scraper import load_competitors
    from pipeline.instagram_research import create_instagram_research_pipeline

    competitors = load_competitors()
    reels_per = args.reels_per
    top_n = args.top

    print(f"\n{'='*60}")
    print(f"  Instagram Competitor Research")
    comp_names = ", ".join(f"@{c['username']}" for c in competitors)
    print(f"  Competitors: {comp_names}")
    print(f"  Reels per competitor: {reels_per} | Top: {top_n}")
    print(f"{'='*60}\n")

    if args.dry_run:
        cost_est = len(competitors) * reels_per * 0.001
        print("DRY RUN - would scrape:")
        for c in competitors:
            print(f"  @{c['username']} ({c.get('followers', '?')} followers) - {reels_per} reels")
        print(f"\nEstimated cost: ~${cost_est:.2f}")
        print(f"Total reels to fetch: {len(competitors) * reels_per}")
        return

    cache = CacheStore() if not args.no_cache else None
    pipeline = create_instagram_research_pipeline()

    context = {
        "reels_per_competitor": reels_per,
        "top_n": top_n,
        "cache": cache,
    }

    result = pipeline.run(context)

    print(f"\n{'='*60}")
    print(f"  Research complete!")
    print(f"  Report: {result.get('report_md_path', 'N/A')}")
    print(f"{'='*60}\n")

    analyzed = result.get("analyzed_reels", [])
    if analyzed:
        print(f"Top {len(analyzed)} reels:\n")
        for reel in analyzed:
            plays = reel.get("plays", 0)
            p_str = f"{plays/1_000_000:.1f}M" if plays >= 1_000_000 else f"{plays/1000:.1f}K" if plays >= 1000 else str(plays)
            likes = reel.get("likes", 0)
            l_str = f"{likes/1_000_000:.1f}M" if likes >= 1_000_000 else f"{likes/1000:.1f}K" if likes >= 1000 else str(likes)

            print(
                f"  {reel['rank']:2d}. [@{reel.get('username', '?')}] "
                f"{reel.get('theme', '?')}"
            )
            print(
                f"      {p_str} plays | {l_str} likes | "
                f"{reel['virality_ratio']:.2f}x viral | "
                f"{reel.get('hook_pattern', '?')}"
            )
            hook = reel.get("hook", "")
            if hook:
                print(f"      \"{hook[:80]}{'...' if len(hook) > 80 else ''}\"")
            print()


def cmd_competitors(args):
    """Manage competitor list."""
    from instagram.scraper import load_competitors, add_competitor, remove_competitor

    if args.list:
        competitors = load_competitors()
        if not competitors:
            print("No competitors tracked. Use --add to add one.")
            return
        print(f"Tracked competitors ({len(competitors)}):\n")
        for c in competitors:
            notes = c.get("notes", "")
            print(f"  @{c['username']} ({c.get('followers', '?')} followers)")
            if notes:
                print(f"    Notes: {notes}")
        return

    if args.add:
        if not args.followers:
            print("ERROR: --followers required with --add")
            return
        add_competitor(args.add, args.followers, args.notes or "")
        return

    if args.remove:
        remove_competitor(args.remove)
        return

    print("Use --list, --add, or --remove")


def cmd_report(args):
    """View Instagram research reports."""
    from output.reporter import find_ig_report

    md_path, json_path = find_ig_report(date=args.date)

    if not md_path:
        print("No report found. Run 'instagram_cli.py research' first.")
        return

    if args.format == "json" and json_path:
        with open(json_path) as f:
            data = json.load(f)
        print(json.dumps(data, indent=2))
    elif args.format == "markdown":
        with open(md_path) as f:
            print(f.read())
    else:
        with open(md_path) as f:
            content = f.read()
        for line in content.split("\n"):
            if line.startswith("## Detailed"):
                break
            print(line)


def cmd_cache(args):
    """Manage the fetch cache."""
    from cache.store import CacheStore

    cache = CacheStore()
    if args.clear:
        cache.clear()
        print("Cache cleared.")
    elif args.stats:
        stats = cache.stats()
        print(f"Cache statistics:")
        print(f"  Total entries:  {stats['total_entries']}")
        print(f"  Active:         {stats['active_entries']}")
        print(f"  Expired:        {stats['expired_entries']}")
        print(f"  Size on disk:   {stats['size_kb']} KB")
        print(f"  TTL:            {stats['ttl_hours']} hours")
    else:
        print("Use --clear or --stats")


def main():
    parser = argparse.ArgumentParser(
        description="Instagram Competitor Research - find top reels and extract content patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")

    # research
    p_res = sub.add_parser("research", help="Run competitor research pipeline")
    p_res.add_argument(
        "--reels-per", type=int, default=30,
        help="Reels to scrape per competitor (default: 30)"
    )
    p_res.add_argument(
        "--top", type=int, default=15,
        help="Number of top reels in report (default: 15)"
    )
    p_res.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be scraped without API calls"
    )
    p_res.add_argument(
        "--no-cache", action="store_true",
        help="Bypass cache (force fresh scrape)"
    )
    p_res.set_defaults(func=cmd_research)

    # competitors
    p_comp = sub.add_parser("competitors", help="Manage tracked competitors")
    p_comp.add_argument("--list", action="store_true", help="List all competitors")
    p_comp.add_argument("--add", help="Add a competitor (username)")
    p_comp.add_argument("--remove", help="Remove a competitor (username)")
    p_comp.add_argument("--followers", type=int, help="Follower count (used with --add)")
    p_comp.add_argument("--notes", help="Notes about the competitor (used with --add)")
    p_comp.set_defaults(func=cmd_competitors)

    # report
    p_rep = sub.add_parser("report", help="View research reports")
    p_rep.add_argument("--latest", action="store_true", help="Show most recent report")
    p_rep.add_argument("--date", help="Report date (YYYY-MM-DD)")
    p_rep.add_argument(
        "--format", choices=["markdown", "json", "summary"],
        default="summary", help="Output format (default: summary)"
    )
    p_rep.set_defaults(func=cmd_report)

    # cache
    p_cache = sub.add_parser("cache", help="Manage fetch cache")
    p_cache.add_argument("--clear", action="store_true")
    p_cache.add_argument("--stats", action="store_true")
    p_cache.set_defaults(func=cmd_cache)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
```

---

### `research/instagram/scraper.py`

Handles all Instagram data fetching. Uses DataPrism as primary API with Apify fallback. **If you use a different scraping service, this is the only file you need to modify.**

```python
"""Scrape Instagram competitor reels via DataPrism REST API (Apify fallback)."""

import json
import os
import time
from datetime import datetime

import requests

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
COMPETITORS_PATH = os.path.join(SCRIPT_DIR, "competitors.json")

DATAPRISM_BASE = "https://platform.dataprism.dev/api/v1"
DATAPRISM_KEY = os.environ.get("DATAPRISM_API_KEY", "")

APIFY_BASE = "https://api.apify.com/v2"
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
APIFY_IG_ACTOR = "apify~instagram-scraper"


def _dataprism_request(endpoint, data, timeout=120):
    """Make an authenticated DataPrism API request."""
    url = f"{DATAPRISM_BASE}{endpoint}"
    headers = {
        "X-API-KEY": DATAPRISM_KEY,
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json=data, timeout=timeout)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"DataPrism request failed: {resp.status_code} {resp.text[:200]}"
        )
    return json.loads(resp.text, strict=False)


def load_competitors():
    """Load the local competitors list."""
    with open(COMPETITORS_PATH) as f:
        data = json.load(f)
    return data.get("competitors", [])


def save_competitors(competitors):
    """Save updated competitors list."""
    with open(COMPETITORS_PATH, "w") as f:
        json.dump({"competitors": competitors}, f, indent=2)
        f.write("\n")


def add_competitor(username, followers, notes=""):
    """Add or update a competitor."""
    competitors = load_competitors()
    username = username.lstrip("@").strip()

    existing = [c for c in competitors if c["username"] == username]
    if existing:
        existing[0]["followers"] = followers
        if notes:
            existing[0]["notes"] = notes
        print(f"Updated @{username} (followers: {followers})")
    else:
        entry = {"username": username, "followers": followers}
        if notes:
            entry["notes"] = notes
        competitors.append(entry)
        print(f"Added @{username} (followers: {followers})")

    save_competitors(competitors)


def remove_competitor(username):
    """Remove a competitor by username."""
    competitors = load_competitors()
    username = username.lstrip("@").strip()
    before = len(competitors)
    competitors = [c for c in competitors if c["username"] != username]
    if len(competitors) < before:
        save_competitors(competitors)
        print(f"Removed @{username}")
    else:
        print(f"@{username} not found in competitor list")


def normalize_reel(raw, username, followers=0):
    """Normalize a raw post/reel from any API into a standard dict.

    This handles multiple response formats. If you swap in a different
    scraping API, you may need to adjust the field names here.
    """
    media_list = raw.get("media", [])
    is_video = any(m.get("type") == "video" for m in media_list) if media_list else raw.get("type") == "video"

    likes = raw.get("likesCount") or raw.get("like_count") or raw.get("likes", 0)
    comments = raw.get("commentsCount") or raw.get("comment_count") or raw.get("comments", 0)
    plays = raw.get("videoPlayCount") or raw.get("play_count") or raw.get("plays") or raw.get("videoViewCount", 0)
    saves = raw.get("savesCount") or raw.get("save_count") or raw.get("saves", 0)

    caption = raw.get("caption") or raw.get("text") or ""
    if isinstance(caption, dict):
        caption = caption.get("text", "")

    timestamp = raw.get("timestamp") or raw.get("taken_at") or raw.get("date") or ""
    if isinstance(timestamp, (int, float)):
        try:
            timestamp = datetime.fromtimestamp(timestamp).isoformat()
        except (OSError, ValueError):
            timestamp = ""

    url = raw.get("url") or raw.get("shortCode", "")
    if url and not url.startswith("http"):
        url = f"https://www.instagram.com/reel/{url}/"

    thumbnail = ""
    if media_list:
        thumbnail = media_list[0].get("url", "")
    if not thumbnail:
        thumbnail = raw.get("displayUrl") or raw.get("thumbnail_url", "")

    return {
        "username": username,
        "followers": followers,
        "caption": caption[:500],
        "likes": int(likes) if likes else 0,
        "comments": int(comments) if comments else 0,
        "plays": int(plays) if plays else 0,
        "saves": int(saves) if saves else 0,
        "is_video": is_video,
        "url": url,
        "thumbnail_url": thumbnail,
        "timestamp": str(timestamp),
    }


def scrape_competitor_reels_dataprism(username, max_reels=30, cache=None):
    """Scrape reels from a single competitor via DataPrism."""
    if not DATAPRISM_KEY:
        raise ValueError("No DataPrism API key. Set DATAPRISM_API_KEY env var.")

    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"ig:{username}:{max_reels}:{today}"
    if cache:
        cached = cache.get(cache_key)
        if cached:
            print(f"    (cached {len(cached)} reels for @{username})")
            return cached

    print(f"    Scraping @{username} via DataPrism ({max_reels} posts)...")
    resp = _dataprism_request("/tools/instagram/scrape", {
        "username": username,
        "posts": max_reels,
    }, timeout=120)

    data = resp.get("data", resp)
    profile = data.get("profile", {})
    followers = profile.get("followers", 0)
    posts = data.get("posts", [])

    reels = []
    for post in posts:
        reel = normalize_reel(post, username, followers)
        reels.append(reel)

    print(f"    Got {len(reels)} posts for @{username} ({followers} followers)")

    if cache and reels:
        cache.set(cache_key, reels)

    return reels


def scrape_competitor_reels_apify(username, max_reels=30, cache=None):
    """Fallback: scrape reels via Apify instagram-scraper."""
    if not APIFY_TOKEN:
        raise ValueError("No Apify token. Set APIFY_TOKEN env var.")

    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"ig-apify:{username}:{max_reels}:{today}"
    if cache:
        cached = cache.get(cache_key)
        if cached:
            print(f"    (cached {len(cached)} reels for @{username} via Apify)")
            return cached

    print(f"    Scraping @{username} via Apify ({max_reels} reels)...")
    run_url = f"{APIFY_BASE}/acts/{APIFY_IG_ACTOR}/run-sync-get-dataset-items"
    params = {"token": APIFY_TOKEN}
    payload = {
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsType": "posts",
        "resultsLimit": max_reels,
    }
    resp = requests.post(run_url, params=params, json=payload, timeout=300)
    if resp.status_code != 201:
        raise RuntimeError(f"Apify error: {resp.status_code} {resp.text[:200]}")

    items = resp.json()
    reels = []
    for item in items:
        reel = normalize_reel(item, username, item.get("ownerFollowerCount", 0))
        reels.append(reel)

    print(f"    Got {len(reels)} posts for @{username} via Apify")

    if cache and reels:
        cache.set(cache_key, reels)

    return reels


def scrape_all_competitors(max_reels_per=30, cache=None, use_apify_fallback=True):
    """Scrape reels from all competitors in competitors.json.

    Tries DataPrism first, falls back to Apify if configured.
    Returns combined list of normalized reel dicts.
    """
    competitors = load_competitors()
    all_reels = []

    for comp in competitors:
        username = comp["username"]
        try:
            reels = scrape_competitor_reels_dataprism(
                username, max_reels=max_reels_per, cache=cache
            )
            if comp.get("followers"):
                for r in reels:
                    if not r["followers"]:
                        r["followers"] = comp["followers"]
            all_reels.extend(reels)
        except Exception as e:
            print(f"    DataPrism failed for @{username}: {e}")
            if use_apify_fallback and APIFY_TOKEN:
                try:
                    reels = scrape_competitor_reels_apify(
                        username, max_reels=max_reels_per, cache=cache
                    )
                    if comp.get("followers"):
                        for r in reels:
                            if not r["followers"]:
                                r["followers"] = comp["followers"]
                    all_reels.extend(reels)
                except Exception as e2:
                    print(f"    Apify fallback also failed for @{username}: {e2}")
            else:
                print(f"    Skipping @{username} (no Apify fallback)")

        time.sleep(1)

    print(f"    Total: {len(all_reels)} reels from {len(competitors)} competitors")
    return all_reels
```

---

### `research/instagram/scorer.py`

Scores and ranks reels using a composite metric: virality (40%), engagement (30%), recency (20%), save rate (10%).

```python
"""Score and rank Instagram reels by engagement and virality."""

from datetime import datetime


def score_reel(reel):
    """Compute performance metrics for a single reel.

    Returns reel dict with added fields:
        virality_ratio   - plays / followers (reach beyond audience)
        engagement_rate  - (likes + comments*3) / plays (depth of engagement)
        save_rate        - saves / plays (bookmark signal)
        recency_boost    - 0-1 boost for recent posts (within 6 months)
        performance      - composite score (0-100)
    """
    plays = reel.get("plays", 0)
    likes = reel.get("likes", 0)
    comments = reel.get("comments", 0)
    saves = reel.get("saves", 0)
    followers = reel.get("followers", 0)

    # Virality: how far beyond existing audience
    virality = plays / followers if followers > 0 else 0

    # Engagement: comments weighted 3x (deeper signal than likes)
    engagement = (likes + comments * 3) / plays if plays > 0 else 0

    # If no play count, fall back to likes-based engagement
    if plays == 0 and followers > 0:
        engagement = (likes + comments * 3) / followers
        virality = likes / followers

    # Save rate: strong signal for share-worthy content
    save_rate = saves / plays if plays > 0 else 0

    # Recency: recent posts get a boost (0-1, linear decay over 6 months)
    recency = 0.5
    timestamp = reel.get("timestamp", "")
    if timestamp:
        try:
            if "T" in str(timestamp):
                pub = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            else:
                pub = datetime.fromisoformat(str(timestamp))
            days_ago = (datetime.now(pub.tzinfo) - pub).days if pub.tzinfo else (datetime.now() - pub).days
            recency = max(0, 1 - days_ago / 180)
        except (ValueError, TypeError):
            pass

    # Normalize to 0-100 scale
    virality_norm = min(100, virality * 20)       # 5x followers = 100
    engagement_norm = min(100, engagement * 2000)  # 5% = 100
    save_norm = min(100, save_rate * 5000)         # 2% save rate = 100
    recency_norm = recency * 100                   # Direct 0-100

    # Composite: virality matters most, then engagement, saves as bonus
    performance = (
        virality_norm * 0.40
        + engagement_norm * 0.30
        + save_norm * 0.10
        + recency_norm * 0.20
    )

    scored = dict(reel)
    scored["virality_ratio"] = round(virality, 3)
    scored["engagement_rate"] = round(engagement, 4)
    scored["save_rate"] = round(save_rate, 4)
    scored["recency_boost"] = round(recency, 2)
    scored["performance"] = round(performance, 1)
    return scored


def score_and_rank(reels, top_n=15):
    """Score all reels and return top N ranked.

    Filters out:
        - Reels with 0 followers (can't compute virality)
        - Reels with < 100 likes (noise floor)

    Returns sorted list by performance descending with rank added.
    """
    scored = []
    for reel in reels:
        if reel.get("followers", 0) <= 0:
            continue
        if reel.get("likes", 0) < 100 and reel.get("plays", 0) < 1000:
            continue
        scored.append(score_reel(reel))

    scored.sort(
        key=lambda r: (r["performance"], r.get("plays", 0), r.get("likes", 0)),
        reverse=True,
    )

    for i, reel in enumerate(scored[:top_n], 1):
        reel["rank"] = i

    print(f"    {len(scored)} scoreable reels -> top {min(top_n, len(scored))} ranked")
    return scored[:top_n]
```

---

### `research/instagram/analyzer.py`

Classifies themes, detects hook patterns, and computes aggregate insights.

```python
"""Analyze Instagram reel captions for hooks, themes, and content patterns."""

import re
from collections import Counter


# Theme categories by keyword signals in captions.
# Customize these to match your niche.
THEME_KEYWORDS = {
    "AI Tools / Automation": [
        "ai", "artificial intelligence", "automate", "automation", "chatgpt",
        "claude", "claude code", "gpt", "openai", "gemini", "copilot",
        "agent", "workflow", "no-code", "low-code", "cursor", "vibe cod",
    ],
    "Marketing / Growth": [
        "marketing", "growth", "leads", "funnel", "ads", "campaign",
        "content strategy", "social media", "engagement", "audience",
        "instagram", "tiktok", "reach", "viral", "algorithm",
    ],
    "Sales / Revenue": [
        "sales", "revenue", "client", "close", "deal", "dm",
        "outreach", "prospect", "cold", "pitch", "booking",
        "high ticket", "convert", "commission",
    ],
    "Entrepreneurship": [
        "entrepreneur", "business", "startup", "agency", "freelanc",
        "founder", "side hustle", "scale", "bootstrap", "solopreneur",
    ],
    "Productivity / Systems": [
        "productiv", "system", "workflow", "notion", "template",
        "organize", "efficiency", "routine", "hack", "shortcut",
        "time management", "sop",
    ],
    "Tutorial / How-To": [
        "how to", "step by step", "tutorial", "guide", "learn",
        "beginner", "walkthrough", "setup", "install", "config",
    ],
    "Finance / Money": [
        "money", "income", "passive", "investing", "wealth",
        "profit", "earn", "cash", "financial", "bank",
    ],
    "Design / Creative": [
        "design", "canva", "photoshop", "figma", "creative",
        "brand", "aesthetic", "visual", "font", "color",
    ],
    "Personal Development": [
        "mindset", "discipline", "habit", "motivation", "success",
        "confidence", "focus", "stoic", "grind",
    ],
}

# Caption hook patterns (first line/sentence patterns)
HOOK_PATTERNS = {
    "Tool Reveal": [
        r"this (?:ai )?tool", r"I found", r"just discovered",
        r"new tool", r"(?:game|life) chang", r"you need this",
    ],
    "Result / Proof": [
        r"\d+[kKmM]?\+?\s*(?:followers|views|leads|clients|sales|revenue)",
        r"(?:made|earned|generated)\s*\$?\d+",
        r"results", r"proof", r"it works",
    ],
    "Contrarian / Myth-Bust": [
        r"stop", r"don'?t", r"you'?re (?:doing it )?wrong",
        r"nobody (?:tells|talks)", r"myth", r"overrated",
        r"unpopular opinion", r"hot take",
    ],
    "How-To / Tutorial": [
        r"how (?:to|I)", r"step[- ]by[- ]step", r"here'?s how",
        r"do this", r"try this", r"the (?:exact|simple) way",
    ],
    "Listicle / Number": [
        r"^\d+\s+", r"\d+\s+(?:ways|tips|tools|apps|things|reasons|hacks)",
        r"top\s+\d+",
    ],
    "Question / Curiosity": [
        r"^(?:did you|have you|do you|why do|what if|ever wonder)",
        r"\?$", r"guess what",
    ],
    "Speed / Shortcut": [
        r"in \d+ (?:seconds?|minutes?|mins?)",
        r"(?:instant|quick|fast|rapid)", r"one click",
        r"in seconds", r"shortcut",
    ],
    "Before / After": [
        r"before.*after", r"vs\.?", r"compared to",
        r"old way.*new way", r"then.*now",
    ],
}


def _extract_hook(caption):
    """Extract the hook (first meaningful line) from a caption."""
    if not caption:
        return ""
    lines = caption.strip().split("\n")
    hook = lines[0].strip()
    if len(hook) < 15 and len(lines) > 1:
        hook = f"{hook} {lines[1].strip()}"
    return hook[:200]


def classify_theme(caption):
    """Classify reel theme from caption keywords."""
    text = caption.lower()
    scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[theme] = score

    if not scores:
        return "Uncategorized"

    return max(scores, key=scores.get)


def detect_hook_pattern(caption):
    """Detect the hook pattern used in the caption opening."""
    if not caption:
        return "General"

    hook = _extract_hook(caption).lower()
    for pattern_name, patterns in HOOK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, hook):
                return pattern_name

    return "General"


def detect_content_format(reel):
    """Infer content format from available metadata."""
    caption = (reel.get("caption") or "").lower()

    if any(kw in caption for kw in ["screen record", "tutorial", "walkthrough", "step by step"]):
        return "Screen Recording"
    if any(kw in caption for kw in ["talking head", "face cam"]):
        return "Talking Head"
    if any(kw in caption for kw in ["carousel", "slide"]):
        return "Carousel-Style"
    if any(kw in caption for kw in ["voiceover", "voice over", "narrat"]):
        return "Voiceover + B-roll"

    return "Unknown"


def analyze_reel(reel):
    """Full analysis of a single reel. Returns reel dict with analysis fields added."""
    caption = reel.get("caption", "")

    analyzed = dict(reel)
    analyzed["hook"] = _extract_hook(caption)
    analyzed["theme"] = classify_theme(caption)
    analyzed["hook_pattern"] = detect_hook_pattern(caption)
    analyzed["content_format"] = detect_content_format(reel)
    analyzed["caption_length"] = len(caption)
    analyzed["has_cta"] = bool(re.search(
        r"(?:follow|save|share|comment|link in bio|dm me|tap|click|swipe)",
        caption.lower(),
    ))
    analyzed["has_emoji"] = bool(re.search(r"[\U0001f300-\U0001f9ff]", caption))
    analyzed["hashtag_count"] = len(re.findall(r"#\w+", caption))
    return analyzed


def analyze_all(ranked_reels):
    """Analyze all ranked reels."""
    return [analyze_reel(r) for r in ranked_reels]


def compute_insights(analyzed_reels):
    """Compute aggregate insights across all analyzed reels.

    Returns dict with:
        top_themes, top_hook_patterns, top_formats,
        avg_caption_length, cta_pct, avg_hashtags,
        theme_avg_performance
    """
    themes = Counter()
    patterns = Counter()
    formats = Counter()
    theme_perf = {}

    for reel in analyzed_reels:
        theme = reel.get("theme", "Uncategorized")
        themes[theme] += 1
        patterns[reel.get("hook_pattern", "General")] += 1
        formats[reel.get("content_format", "Unknown")] += 1

        if theme not in theme_perf:
            theme_perf[theme] = []
        theme_perf[theme].append(reel.get("performance", 0))

    theme_avg = {
        theme: round(sum(scores) / len(scores), 1)
        for theme, scores in theme_perf.items()
    }

    total_caption_len = sum(r.get("caption_length", 0) for r in analyzed_reels)
    avg_caption = round(total_caption_len / len(analyzed_reels), 0) if analyzed_reels else 0

    num_with_cta = sum(1 for r in analyzed_reels if r.get("has_cta"))
    total_hashtags = sum(r.get("hashtag_count", 0) for r in analyzed_reels)
    avg_hashtags = round(total_hashtags / len(analyzed_reels), 1) if analyzed_reels else 0

    return {
        "top_themes": themes.most_common(10),
        "top_hook_patterns": patterns.most_common(10),
        "top_formats": formats.most_common(10),
        "avg_caption_length": avg_caption,
        "cta_pct": round(num_with_cta / len(analyzed_reels) * 100, 1) if analyzed_reels else 0,
        "avg_hashtags": avg_hashtags,
        "theme_avg_performance": theme_avg,
    }
```

---

### `research/pipeline/base.py`

Minimal pipeline framework - steps run in sequence, sharing a context dict.

```python
"""Research pipeline framework."""

from abc import ABC, abstractmethod


class ResearchStep(ABC):
    """A single step in the research pipeline."""

    @property
    @abstractmethod
    def name(self):
        ...

    @abstractmethod
    def execute(self, context):
        """Execute step, reading/writing to shared context dict."""
        ...


class ResearchPipeline:
    """Ordered sequence of research steps."""

    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

    def run(self, initial_context):
        context = dict(initial_context)
        for step in self.steps:
            print(f"  [{step.name}]")
            context = step.execute(context)
        return context
```

---

### `research/pipeline/instagram_research.py`

Wires the 4 pipeline steps together: Scrape, Score, Analyze, Report.

```python
"""Instagram competitor research pipeline.

Steps:
    1. ScrapeCompetitors - scrape reels from all tracked competitors
    2. ScoreAndRank - compute virality + engagement metrics and rank
    3. AnalyzeContent - extract hooks, themes, patterns from captions
    4. GenerateReport - save markdown + JSON report
"""

from pipeline.base import ResearchStep, ResearchPipeline


class ScrapeCompetitorsStep(ResearchStep):
    @property
    def name(self):
        return "Scrape Competitors"

    def execute(self, context):
        from instagram.scraper import scrape_all_competitors

        max_reels = context.get("reels_per_competitor", 30)
        cache = context.get("cache")

        reels = scrape_all_competitors(
            max_reels_per=max_reels, cache=cache
        )

        context["raw_reels"] = reels
        return context


class ScoreAndRankStep(ResearchStep):
    @property
    def name(self):
        return "Score & Rank"

    def execute(self, context):
        from instagram.scorer import score_and_rank

        reels = context["raw_reels"]
        top_n = context.get("top_n", 15)

        ranked = score_and_rank(reels, top_n=top_n)

        context["ranked_reels"] = ranked
        return context


class AnalyzeContentStep(ResearchStep):
    @property
    def name(self):
        return "Analyze Content"

    def execute(self, context):
        from instagram.analyzer import analyze_all, compute_insights

        ranked = context["ranked_reels"]
        analyzed = analyze_all(ranked)
        insights = compute_insights(analyzed)

        print(f"    Themes found: {', '.join(t for t, _ in insights['top_themes'][:5])}")
        print(f"    Top hooks: {', '.join(p for p, _ in insights['top_hook_patterns'][:3])}")
        print(f"    Avg caption length: {insights['avg_caption_length']} chars")

        context["analyzed_reels"] = analyzed
        context["insights"] = insights
        return context


class GenerateReportStep(ResearchStep):
    @property
    def name(self):
        return "Generate Report"

    def execute(self, context):
        from output.reporter import save_ig_reports

        analyzed = context["analyzed_reels"]
        insights = context["insights"]

        from instagram.scraper import load_competitors
        competitors = load_competitors()

        metadata = {
            "competitors": [c["username"] for c in competitors],
            "reels_per_competitor": context.get("reels_per_competitor", 30),
            "total_reels_found": len(context.get("raw_reels", [])),
            "top_n": context.get("top_n", 15),
        }

        md_path, json_path = save_ig_reports(analyzed, insights, metadata)
        print(f"    Report: {md_path}")

        context["report_md_path"] = md_path
        context["report_json_path"] = json_path
        return context


def create_instagram_research_pipeline():
    """Create the full Instagram competitor research pipeline."""
    return ResearchPipeline(
        name="Instagram Competitor Research",
        steps=[
            ScrapeCompetitorsStep(),
            ScoreAndRankStep(),
            AnalyzeContentStep(),
            GenerateReportStep(),
        ],
    )
```

---

### `research/output/reporter.py`

Generates markdown and JSON reports from analyzed data.

```python
"""Generate Instagram research reports and save as markdown + JSON."""

import json
import os
import re
from datetime import datetime

REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports"
)


def _fmt_count(n):
    """Format count: 438574 -> '438.6K'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def generate_ig_markdown(analyzed_reels, insights, metadata):
    """Generate an Instagram research markdown report."""
    now = datetime.now()
    competitors = metadata.get("competitors", [])
    total_found = metadata.get("total_reels_found", 0)

    lines = []
    lines.append("# Instagram Competitor Research Report")
    lines.append("")
    lines.append(
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M')} | "
        f"**Reels Scraped:** {total_found} | "
        f"**Top:** {len(analyzed_reels)}"
    )
    lines.append(f"**Competitors:** {', '.join(f'@{c}' for c in competitors)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append(f"## Top {len(analyzed_reels)} Reels by Performance")
    lines.append("")
    lines.append("| # | Account | Hook | Plays | Likes | Viral | Engage | Theme |")
    lines.append("|---|---------|------|-------|-------|-------|--------|-------|")

    for reel in analyzed_reels:
        rank = reel.get("rank", "?")
        username = f"@{reel.get('username', '?')}"
        hook = (reel.get("hook") or "")[:45]
        if len(reel.get("hook") or "") > 45:
            hook += "..."
        plays = _fmt_count(reel.get("plays", 0))
        likes = _fmt_count(reel.get("likes", 0))
        viral = f"{reel.get('virality_ratio', 0):.2f}x"
        engage = f"{reel.get('engagement_rate', 0) * 100:.1f}%"
        theme = reel.get("theme", "?")

        lines.append(
            f"| {rank} | {username} | {hook} | {plays} | {likes} | {viral} | {engage} | {theme} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed breakdowns
    lines.append("## Detailed Breakdowns")
    lines.append("")

    for reel in analyzed_reels:
        rank = reel.get("rank", "?")
        username = reel.get("username", "?")
        followers = reel.get("followers", 0)
        plays = reel.get("plays", 0)
        likes = reel.get("likes", 0)
        comments = reel.get("comments", 0)
        saves = reel.get("saves", 0)
        virality = reel.get("virality_ratio", 0)
        engagement = reel.get("engagement_rate", 0)
        save_rate = reel.get("save_rate", 0)
        perf = reel.get("performance", 0)
        theme = reel.get("theme", "?")
        hook_pattern = reel.get("hook_pattern", "?")
        content_format = reel.get("content_format", "?")
        hook = reel.get("hook", "")
        caption = reel.get("caption", "")
        url = reel.get("url", "")
        timestamp = reel.get("timestamp", "")[:10]

        lines.append(f"### {rank}. @{username}")
        lines.append("")
        if hook:
            lines.append(f"> {hook}")
            lines.append("")
        lines.append(f"- **Followers:** {_fmt_count(followers)}")
        lines.append(f"- **Plays:** {_fmt_count(plays)} | **Likes:** {_fmt_count(likes)} | **Comments:** {_fmt_count(comments)} | **Saves:** {_fmt_count(saves)}")
        lines.append(f"- **Virality:** {virality:.3f}x | **Engagement:** {engagement * 100:.1f}% | **Save Rate:** {save_rate * 100:.2f}% | **Score:** {perf}")
        lines.append(f"- **Theme:** {theme} | **Hook Pattern:** {hook_pattern} | **Format:** {content_format}")
        lines.append(f"- **Posted:** {timestamp}")
        if url:
            lines.append(f"- **URL:** {url}")
        if caption and len(caption) > len(hook) + 10:
            lines.append(f"- **Caption preview:** {caption[:200]}...")
        lines.append("")

    # Insights
    lines.append("---")
    lines.append("")
    lines.append("## Insights")
    lines.append("")

    theme_perf = insights.get("theme_avg_performance", {})
    if theme_perf:
        lines.append("### Theme Performance")
        lines.append("")
        lines.append("| Theme | Avg Score | Count |")
        lines.append("|-------|-----------|-------|")
        for theme, count in insights.get("top_themes", []):
            avg = theme_perf.get(theme, 0)
            lines.append(f"| {theme} | {avg} | {count} |")
        lines.append("")

    top_hooks = insights.get("top_hook_patterns", [])
    if top_hooks:
        lines.append("### Hook Patterns")
        lines.append("")
        for pattern, count in top_hooks:
            lines.append(f"- **{pattern}:** {count} reels")
        lines.append("")

    top_formats = insights.get("top_formats", [])
    if top_formats:
        lines.append("### Content Formats")
        lines.append("")
        for fmt, count in top_formats:
            lines.append(f"- **{fmt}:** {count} reels")
        lines.append("")

    lines.append("### Caption Analysis")
    lines.append(f"- **Avg caption length:** {insights.get('avg_caption_length', 0)} chars")
    lines.append(f"- **Reels with CTA:** {insights.get('cta_pct', 0)}%")
    lines.append(f"- **Avg hashtags:** {insights.get('avg_hashtags', 0)}")
    lines.append("")

    return "\n".join(lines)


def save_ig_reports(analyzed_reels, insights, metadata):
    """Save Instagram research reports (MD + JSON). Returns (md_path, json_path)."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    md_content = generate_ig_markdown(analyzed_reels, insights, metadata)
    md_path = os.path.join(REPORTS_DIR, f"ig_{date_str}_competitor-research.md")
    with open(md_path, "w") as f:
        f.write(md_content)

    json_data = {
        "metadata": {
            **metadata,
            "generated_at": datetime.now().isoformat(),
        },
        "reels": analyzed_reels,
        "insights": {
            **insights,
            "top_themes": [{"theme": t, "count": c} for t, c in insights.get("top_themes", [])],
            "top_hook_patterns": [{"pattern": p, "count": c} for p, c in insights.get("top_hook_patterns", [])],
            "top_formats": [{"format": f, "count": c} for f, c in insights.get("top_formats", [])],
        },
    }
    json_path = os.path.join(REPORTS_DIR, f"ig_{date_str}_competitor-research.json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2, default=str)

    return md_path, json_path


def find_ig_report(date=None):
    """Find an Instagram report by date (or latest). Returns (md_path, json_path) or (None, None)."""
    if not os.path.exists(REPORTS_DIR):
        return None, None

    md_files = sorted(
        [f for f in os.listdir(REPORTS_DIR) if f.startswith("ig_") and f.endswith(".md")],
        reverse=True,
    )

    if date:
        for f in md_files:
            if f.startswith(f"ig_{date}"):
                md_path = os.path.join(REPORTS_DIR, f)
                json_path = md_path.replace(".md", ".json")
                return md_path, json_path if os.path.exists(json_path) else None
        return None, None

    if md_files:
        md_path = os.path.join(REPORTS_DIR, md_files[0])
        json_path = md_path.replace(".md", ".json")
        return md_path, json_path if os.path.exists(json_path) else None

    return None, None
```

---

### `research/cache/store.py`

SQLite-based cache to avoid re-fetching the same data within a 4-hour window.

```python
"""SQLite-based cache for fetched data. Avoids re-fetching within TTL."""

import json
import os
import sqlite3
import time

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "cache.db"
)

DEFAULT_TTL = 4 * 60 * 60  # 4 hours


class CacheStore:
    """Simple key-value cache backed by SQLite with TTL expiry."""

    def __init__(self, db_path=DEFAULT_DB_PATH, ttl=DEFAULT_TTL):
        self.db_path = db_path
        self.ttl = ttl
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_table()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        with self._conn() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(key TEXT PRIMARY KEY, value TEXT, ts REAL)"
            )

    def get(self, key):
        """Return cached value if exists and not expired, else None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value, ts FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        value, ts = row
        if time.time() - ts > self.ttl:
            return None
        return json.loads(value)

    def set(self, key, value):
        """Store value with current timestamp."""
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, ts) VALUES (?, ?, ?)",
                (key, json.dumps(value), time.time())
            )

    def clear(self):
        """Delete all cached entries."""
        with self._conn() as conn:
            conn.execute("DELETE FROM cache")

    def stats(self):
        """Return cache statistics."""
        now = time.time()
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            expired = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE ? - ts > ?",
                (now, self.ttl)
            ).fetchone()[0]
        size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        return {
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired,
            "size_kb": round(size_bytes / 1024, 1),
            "ttl_hours": self.ttl / 3600,
        }
```

---

### `research/competitors.json`

Your tracked competitor list. Start with a few accounts in your niche:

```json
{
  "competitors": [
    {
      "username": "example_account",
      "followers": 100000,
      "notes": "AI tools, automation content"
    }
  ]
}
```

### `research/data/config.json`

Default pipeline settings:

```json
{
  "default_reels_per_competitor": 30,
  "default_top_n": 15,
  "min_likes_threshold": 100,
  "min_plays_threshold": 1000
}
```

---

## Usage

Once everything is set up, use the slash command in Claude Code:

```
/instagram-research              # Run full pipeline + get content ideas
/instagram-research list         # Show tracked competitors
/instagram-research add garyvee 14000000 "Marketing, entrepreneurship"
/instagram-research remove garyvee
/instagram-research report       # View latest report
```

Or run the Python CLI directly:

```bash
python3 research/instagram_cli.py research --reels-per 50 --top 20
python3 research/instagram_cli.py research --dry-run
python3 research/instagram_cli.py competitors --list
python3 research/instagram_cli.py report --latest --format markdown
python3 research/instagram_cli.py cache --stats
```

---

## How the Scoring Works

Each reel gets a **composite performance score (0-100)** based on four signals:

| Signal | Weight | What it Measures | 100 = |
|--------|--------|-----------------|-------|
| **Virality Ratio** | 40% | plays / followers | 5x follower reach |
| **Engagement Rate** | 30% | (likes + comments*3) / plays | 5% engagement |
| **Recency** | 20% | Linear decay over 6 months | Published today |
| **Save Rate** | 10% | saves / plays | 2% save rate |

Comments are weighted 3x because they're a deeper engagement signal than likes. The noise floor filters out reels with fewer than 100 likes or 1,000 plays.

---

## Customizing for Your Niche

The main thing to customize is the **theme keywords** and **hook patterns** in `analyzer.py`. The defaults cover AI/tech/marketing/entrepreneurship. If you're in fitness, real estate, cooking, etc., swap in keywords that match your content categories.

You can also adjust:
- **Scoring weights** in `scorer.py` (maybe save rate matters more in your niche)
- **Noise floor thresholds** in `scorer.py` (raise for bigger accounts, lower for micro-niches)
- **Scraping API** in `scraper.py` (swap DataPrism/Apify for whatever service you use)

---

## Swapping the Scraping API

The pipeline is designed to work with any Instagram scraping service. If you use a different provider:

1. Edit `scraper.py` and modify the `scrape_competitor_reels_*` functions to call your API
2. Make sure each reel returns at least: `likes`, `comments`, `plays`, `saves`, `caption`, `timestamp`, `url`
3. The `normalize_reel()` function handles field name variations - add your API's field names there

The rest of the pipeline (scoring, analysis, reporting) works with the normalized data regardless of source.
