#!/usr/bin/env python3
"""
Schedule Instagram content through the Metricool API.

    python3 publisher/schedule.py reel     video.mp4 --caption "..." --at 2026-11-01T19:00
    python3 publisher/schedule.py trial    video.mp4 --caption "..." --at ...   # trial reel, non-followers only
    python3 publisher/schedule.py carousel slide_1.png slide_2.png ... --caption "..." --at ...
    python3 publisher/schedule.py story    frame_1.png frame_2.png ... --at ...  # one post, frames in order

By default posts are created as DRAFTS in Metricool so you can check them there.
Add --publish to schedule them for automatic publishing.

Spec: docs/guides/Instagram_scheduling.md
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from envfile import load_env, require  # noqa: E402

API = "https://app.metricool.com/api/v2/scheduler/posts"
LOG_PATH = HERE / "schedule_log.json"

# instagramData.type per content kind. TRIAL_REEL and POST are documented in the
# guide; REEL and STORY must be confirmed with a first --draft run (see README).
IG_TYPES = {"reel": "REEL", "trial": "TRIAL_REEL", "carousel": "POST", "story": "STORY"}


def upload(path):
    """Upload to tmpfiles.org (public for ~60 min) and return a direct download URL."""
    with open(path, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=180)
    r.raise_for_status()
    return r.json()["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")


def fingerprint(kind, files):
    h = hashlib.sha256(kind.encode())
    for p in files:
        h.update(Path(p).read_bytes())
    return h.hexdigest()[:16]


def load_log():
    return json.loads(LOG_PATH.read_text(encoding="utf-8")) if LOG_PATH.exists() else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=IG_TYPES)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--caption", default="")
    ap.add_argument("--at", required=True, help="местное время, напр. 2026-11-01T19:00")
    ap.add_argument("--publish", action="store_true", help="опубликовать автоматически (без флага: черновик)")
    ap.add_argument("--force", action="store_true", help="разрешить повторную отправку тех же файлов")
    args = ap.parse_args()

    for p in args.files:
        if not Path(p).exists():
            raise SystemExit(f"Файл не найден: {p}")
    if args.kind in ("reel", "trial") and len(args.files) != 1:
        raise SystemExit("Для рилса нужен ровно один видеофайл.")

    user_id, blog_id, token = require("METRICOOL_USER_ID", "METRICOOL_BLOG_ID", "METRICOOL_API_TOKEN")
    load_env()
    tz = os.environ.get("TIMEZONE", "Asia/Bishkek")
    when = datetime.fromisoformat(args.at)

    log = load_log()
    fp = fingerprint(args.kind, args.files)
    if not args.force and any(e["fingerprint"] == fp for e in log):
        raise SystemExit("Эти файлы уже отправлялись (см. publisher/schedule_log.json). Добавь --force, если это намеренно.")

    urls = []
    for p in args.files:
        print(f"Загружаю {p}...")
        urls.append(upload(p))
        time.sleep(1)

    ig_data = {"type": IG_TYPES[args.kind]}
    if args.kind == "trial":
        ig_data["shareTrialAutomatically"] = False

    body = {
        "text": args.caption,
        "publicationDate": {"dateTime": when.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": tz},
        "draft": not args.publish,
        "autoPublish": args.publish,
        "saveExternalMediaFiles": True,
        "providers": [{"network": "INSTAGRAM"}],
        "instagramData": ig_data,
        "media": urls,
    }
    r = requests.post(API, params={"userId": user_id, "blogId": blog_id},
                      headers={"X-Mc-Auth": token, "Content-Type": "application/json"},
                      json=body, timeout=60)
    if r.status_code not in (200, 201):
        # Never retry blindly: the post may exist anyway. Check Metricool first.
        raise SystemExit(f"Metricool ответил {r.status_code}: {r.text[:300]}\n"
                         "Не отправляй повторно, пока не проверишь планировщик в Metricool.")

    data = r.json().get("data", {})
    post_id = data.get("id") if isinstance(data, dict) else None
    log.append({"fingerprint": fp, "kind": args.kind, "files": args.files, "at": args.at,
                "timezone": tz, "draft": not args.publish, "metricool_post_id": post_id,
                "created": datetime.now().isoformat(timespec="seconds")})
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    status = "запланирован" if args.publish else "сохранён как черновик"
    print(f"Готово: {args.kind} {status} на {args.at} ({tz}). ID в Metricool: {post_id}")


if __name__ == "__main__":
    main()
