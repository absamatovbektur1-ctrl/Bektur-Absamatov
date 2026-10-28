#!/usr/bin/env python3
"""
Competitor Radar: find reels that beat their creator's own median views.

    python3 radar/radar.py              # fetch via HikerAPI, score, write picklist.md
    python3 radar/radar.py --rescore    # re-score the latest cache, no API calls
    python3 radar/radar.py --dry-run    # show what would be fetched

Spec: docs/guides/Competitor-Radar.md
"""

import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from envfile import require  # noqa: E402

COHORT_PATH = HERE / "cohort.json"
CACHE_DIR = HERE / "cache"
PICKLIST_PATH = HERE / "picklist.md"

API = "https://api.hikerapi.com"
REELS_PER_CREATOR = 40

# Scoring. Tuned for a small niche (KG business creators): start low, then
# adjust after the first run using the distribution the script prints.
WINDOW_MIN_AGE_H = 72        # younger than 3 days: still collecting views
WINDOW_MAX_AGE_D = 30        # older than 30 days: stale topic
MIN_RATIO = 5.0              # primary bar: 5x the creator's own median
HYBRID_RATIO = 3.0           # secondary bar: 3x is enough...
HYBRID_MIN_VIEWS = 20_000    # ...when the reach is real
ABS_FLOOR_VIEWS = 10_000     # every qualifier needs real reach


class AuthError(Exception):
    pass


def hiker_get(path, params, key):
    for attempt in range(3):
        resp = requests.get(API + path, params=params,
                            headers={"x-access-key": key, "accept": "application/json"},
                            timeout=60)
        if resp.status_code in (401, 403):
            raise AuthError(f"HikerAPI {resp.status_code}: проверь HIKER_API_KEY и баланс. {resp.text[:200]}")
        if resp.status_code == 404:
            return None
        if resp.status_code >= 500:
            time.sleep(2 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"HikerAPI {path}: сервер не отвечает после 3 попыток")


def fetch_creator(username, key):
    profile = hiker_get("/v1/user/by/username", {"username": username}, key)
    if not profile or not profile.get("pk"):
        print(f"  @{username}: не найден (проверь ник)")
        return None
    followers = profile.get("follower_count", 0)
    clips, cursor = [], None
    while len(clips) < REELS_PER_CREATOR:
        params = {"user_id": profile["pk"]}
        if cursor:
            params["end_cursor"] = cursor
        page = hiker_get("/v1/user/clips/chunk", params, key)
        if not page or not isinstance(page, list) or not page[0]:
            break
        items, cursor = page[0], page[1] if len(page) > 1 else None
        clips.extend(items)
        if not cursor:
            break
        time.sleep(0.5)
    print(f"  @{username}: {len(clips)} рилсов, {followers:,} подписчиков")
    return {"followers": followers, "clips": clips[:REELS_PER_CREATOR]}


def normalize(clip):
    if not (clip.get("media_type") == 2 or clip.get("product_type") == "clips"):
        return None
    taken = clip.get("taken_at")
    if isinstance(taken, str):
        try:
            taken = datetime.fromisoformat(taken.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    if not taken:
        return None
    caption = clip.get("caption_text")
    if caption is None and isinstance(clip.get("caption"), dict):
        caption = clip["caption"].get("text")
    return {
        "views": clip.get("play_count") or clip.get("view_count") or 0,
        "likes": clip.get("like_count") or 0,
        "comments": clip.get("comment_count") or 0,
        "taken_at": float(taken),
        "caption": (caption or "").strip(),
        "url": f"https://www.instagram.com/reel/{clip.get('code')}/",
    }


def find_outliers(reels_by_creator):
    now = time.time()
    outliers, medians = [], {}
    for creator, reels in reels_by_creator.items():
        window = [r for r in reels
                  if WINDOW_MIN_AGE_H * 3600 <= now - r["taken_at"] <= WINDOW_MAX_AGE_D * 86400]
        if len(window) < 5:
            continue
        median = statistics.median(r["views"] for r in window) or 1
        medians[creator] = int(median)
        for r in window:
            ratio = r["views"] / median
            beats_bar = ratio >= MIN_RATIO or (ratio >= HYBRID_RATIO and r["views"] >= HYBRID_MIN_VIEWS)
            if beats_bar and r["views"] >= ABS_FLOOR_VIEWS:
                outliers.append({**r, "creator": creator, "ratio": round(ratio, 1),
                                 "median": int(median)})
    return sorted(outliers, key=lambda r: r["ratio"], reverse=True), medians


def fmt(n):
    return f"{n / 1_000_000:.1f}M" if n >= 1_000_000 else f"{n / 1000:.0f}k" if n >= 1000 else str(n)


def write_picklist(outliers, medians):
    lines = [f"# Radar pick list - {datetime.now():%Y-%m-%d}", "",
             "| # | Ratio | Views | Creator | О чём | Link | Pick? |",
             "|---|-------|-------|---------|-------|------|-------|"]
    for i, r in enumerate(outliers, 1):
        about = " ".join(r["caption"].split())[:70].replace("|", "/")
        lines.append(f"| {i} | {r['ratio']}x | {fmt(r['views'])} | @{r['creator']} | {about} | {r['url']} |  |")
    lines += ["", "## Медианы просмотров по авторам (окно 3–30 дней)", ""]
    for creator, m in sorted(medians.items(), key=lambda x: -x[1]):
        lines.append(f"- @{creator}: {fmt(m)}")
    lines += ["", "## Почему выстрелило / подходит ли мне", "",
              "_Claude дописывает разбор для каждой строки после запуска._", ""]
    PICKLIST_PATH.write_text("\n".join(lines), encoding="utf-8")


def latest_cache():
    files = sorted(CACHE_DIR.glob("raw_*.json"))
    if not files:
        raise SystemExit("Кэша нет. Сначала запусти без --rescore.")
    return json.loads(files[-1].read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rescore", action="store_true", help="пересчитать последний кэш без запросов к API")
    ap.add_argument("--dry-run", action="store_true", help="только показать, что будет скачано")
    args = ap.parse_args()

    cohort = json.loads(COHORT_PATH.read_text(encoding="utf-8"))["creators"]

    if args.dry_run:
        print(f"{len(cohort)} авторов x ~4 запроса = ~{len(cohort) * 4} запросов к HikerAPI")
        for c in cohort:
            print(f"  @{c['username']}  {c.get('notes', '')}")
        return

    if args.rescore:
        raw = latest_cache()
    else:
        (key,) = require("HIKER_API_KEY")
        raw = {}
        print(f"Сканирую {len(cohort)} авторов...")
        for c in cohort:
            try:
                data = fetch_creator(c["username"], key)
            except AuthError as e:
                raise SystemExit(str(e))
            except Exception as e:  # one broken account must not stop the run
                print(f"  @{c['username']}: ошибка {e}")
                continue
            if data:
                raw[c["username"]] = data
        CACHE_DIR.mkdir(exist_ok=True)
        cache_path = CACHE_DIR / f"raw_{datetime.now():%Y-%m-%d_%H%M}.json"
        cache_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        print(f"Кэш: {cache_path}")

    reels_by_creator = {}
    for creator, data in raw.items():
        reels_by_creator[creator] = [r for r in map(normalize, data["clips"]) if r]

    outliers, medians = find_outliers(reels_by_creator)
    write_picklist(outliers, medians)

    print(f"\nНайдено выбросов: {len(outliers)}. Список: {PICKLIST_PATH}\n")
    for i, r in enumerate(outliers[:10], 1):
        print(f"{i:2d}. {r['ratio']:>5}x  {fmt(r['views']):>6}  @{r['creator']:<22} {' '.join(r['caption'].split())[:60]}")
    if medians:
        print("\nМедианы авторов:", ", ".join(f"@{c} {fmt(m)}" for c, m in sorted(medians.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
