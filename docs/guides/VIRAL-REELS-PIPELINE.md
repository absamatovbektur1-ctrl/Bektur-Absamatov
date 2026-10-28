# Viral Reels Pipeline - Setup Guide

A complete pipeline for **remaking** viral reels from other creators using Claude Code. Drop a public Instagram reel URL in, and the pipeline downloads the source, rips the audio, OCRs the on-screen text, waits for your own B-roll clip, and renders a finished reel that uses the original trending audio + your footage + a pixel-perfect text overlay matching the source.

This is the technical blueprint. Personal identifiers, brand handles, and account IDs have all been stripped so you can adapt it to your own setup. Drop this file into your Claude Code workspace, follow the setup, and you'll have a system that takes any viral reel URL and outputs a finished, scheduled remake ready to publish.

---

## What This Pipeline Does

The format being remade is the most common viral reel template on Instagram right now: aspirational/lifestyle B-roll + trending audio + one static text block (POV hooks, declarative claims, bold lifestyle statements). High-leverage content that's cheap to produce when the recipe is right.

Drop a public IG reel URL in and the pipeline:

1. Downloads the source reel with yt-dlp
2. Rips the audio track (lossless, so you stay on trending audio)
3. Extracts the first frame for OCR reference
4. Reads the on-screen text verbatim (Claude reads the image directly, no OCR API needed)
5. Asks you for a B-roll clip from your own footage library
6. Trims the clip to exactly match source duration
7. Renders the hook text as a transparent PNG (Instagram Sans Bold, pixel-tuned)
8. Composites everything together at 1080x1920, H.264, ready for IG
9. Optionally schedules the post via Metricool as a trial reel

The whole thing runs through Claude Code as a slash command. You say `/viral-reels new <ig-url>` and it walks through every stage, pausing at the points where you actually need to make a judgment call (approve the OCR'd text, pick a B-roll clip).

**Not for** talking-head content. This pipeline is specifically for the B-roll + music + static text format.

---

## Prerequisites

Install these on your machine first (macOS instructions, adapt for Linux/Windows):

```bash
# FFmpeg (for video processing)
brew install ffmpeg

# yt-dlp (for downloading Instagram reels)
brew install yt-dlp

# Python 3.10+ (for the scheduler, optional)
python3 --version  # confirm you have it
```

**For the hook text rendering you need macOS Swift** (preinstalled on any Mac with Xcode Command Line Tools). FFmpeg's `drawtext` filter can render text but it picks weird font metrics, especially for OTF fonts. We render hook text as a PNG via Swift/AppKit for pixel-perfect control. If you're on Linux/Windows, you can substitute Pillow (Python) with similar logic, but the Swift renderer is what's documented here.

### The font

The render recipe is locked to **Instagram Sans Bold**. Meta publishes the font for free. Download it from their brand guidelines page or search "Instagram Sans Bold ttf" and grab the official file. Install it to your user font folder:

```bash
cp "Instagram Sans Bold.ttf" ~/Library/Fonts/
atsutil databases -removeUser   # force font registry refresh on macOS
```

The renderer auto-registers from `~/Library/Fonts` on every invocation, so once it's there you're set.

---

## Folder Structure

Create this structure in your workspace:

```
your-workspace/
├── .claude/
│   └── commands/
│       └── viral-reels.md            # Slash command entry point
├── viral-reels/
│   ├── SKILL.md                       # Full pipeline reference for Claude
│   ├── render_text.swift              # Text overlay renderer
│   ├── scheduler.py                   # Optional: auto-scheduler for Metricool
│   ├── tracker.json                   # Remake database (auto-managed)
│   ├── b-roll/                        # Your own B-roll library
│   ├── fonts/
│   │   └── Instagram Sans Bold.ttf    # The font file
│   └── batch-YYYY-MM-DD/              # One folder per remake batch
│       ├── source.mp4                 # Downloaded source reel
│       ├── source.info.json           # Source metadata
│       ├── audio.m4a                  # Ripped audio
│       ├── source-frame.png           # First frame for OCR
│       ├── clip-trimmed.mp4           # Your B-roll, trimmed to duration
│       └── final/
│           ├── 01-hook.png            # Rendered text overlay
│           └── 01-<slug>.mp4          # Finished reel
```

---

## Setup: Paste This Into Claude Code

When you first paste this file into a Claude Code project, tell Claude:

> "Set up the viral reels pipeline. Create the folder structure, save the scripts from this file, and prepare an empty tracker.json."

Claude will read the file, create the directories, save the four artifacts below, and tell you it's ready. From then on you just send IG URLs.

---

## Artifact 1: The Slash Command

Save this as `.claude/commands/viral-reels.md`:

```markdown
# Viral Reels Pipeline

Orchestrate the viral reels remake pipeline. Request: $ARGUMENTS

## Instructions

Read the SKILL.md and tracker.json to understand the full pipeline and current state:

1. `viral-reels/SKILL.md` - Full pipeline reference (download, OCR, render recipe, scheduling)
2. `viral-reels/tracker.json` - Remake database with statuses and performance data

## Session Start

1. Read SKILL.md and tracker.json
2. Summarize current state: how many clips at each status, which need attention
3. Execute the user's request

## Common Requests

- **"new <ig-url>"** - Run stages 1-3 in one go (download, audio rip, frame extract, OCR), create tracker entry at status `downloaded`, propose verbatim on-screen text for approval, then ask for the B-roll clip.
- **"remake <id> --clip <path>"** - Stage 4-6: trim clip to source duration, render hook PNG, composite with audio, present output + side-by-side comparison.
- **"schedule <id>"** - Run the scheduler (if configured) or upload manually.
- **"status"** - Show tracker summary by status and recent performance.

## Pipeline Rules (non-negotiable)

- **Font**: Always Instagram Sans Bold at 50pt with 5px black stroke. White fill. Two-pass render (stroke + fill separate).
- **Position**: Top of text at y=440 on a 1920-tall canvas. Center horizontally.
- **Audio**: Always rip from source. Never replace with your own music (defeats the point of remaking trending audio).
- **Output**: 1080x1920 H.264 CRF 18. Always re-mux to strip edit list (fixes black first frame).
- **Caption**: Never copy the original creator's caption verbatim. Rewrite in your own voice.
- **Tracker**: Update status and relevant fields after each completed stage.
- **Per-batch directory**: One source URL = one batch. Naming: `batch-YYYY-MM-DD/`.
```

---

## Artifact 2: The SKILL.md

Save this as `viral-reels/SKILL.md`. This is the file Claude reads to understand the full pipeline:

````markdown
# Viral Reels Pipeline

## What This Is

End-to-end pipeline for remaking viral reels from other creators. Input: a public Instagram reel URL. Output: an Instagram-ready reel that uses your own B-roll, the original ripped audio, and an exact-style text overlay matching the source.

## Pipeline Overview

```
Source IG reel URL
     |
     v
[1] DOWNLOAD - yt-dlp the source reel
     -> source.mp4, source.info.json
     |
     v
[2] EXTRACT - rip audio, probe metadata, extract first frame
     -> audio.m4a, source-frame.png, duration
     |
     v
[3] OCR - read on-screen text from the frame (Claude reads it directly)
     -> propose verbatim text + line breaks for approval
     |
     v
[4] WAIT FOR CLIP - user supplies a B-roll clip
     -> probe clip, trim to exact source duration
     |
     v
[5] RENDER HOOK - generate text overlay PNG (Swift/AppKit, Instagram Sans Bold)
     -> hook.png
     |
     v
[6] COMPOSITE - upscale clip + overlay hook + ripped audio
     -> final-NN.mp4 (1080x1920 H.264)
     |
     v
[7] CAPTION + SCHEDULE - write IG caption, schedule on Metricool as TRIAL_REEL
     -> tracker updated, scheduled
     |
     v
[8] MONITOR - track performance, promote winners
     -> trial metrics, optional promotion
```

## The Locked-In Render Recipe

These values were pixel-tuned by overlaying the render on top of an original frame and iterating until they matched. Don't change without re-validating.

| Parameter | Value |
|-----------|-------|
| Output canvas | 1080x1920 (9:16) |
| Font | **Instagram Sans Bold** (`InstagramSans-Bold`) |
| Font size | **50pt** |
| Font color | White fill (`#FFFFFF`) + 5px black stroke |
| Stroke render | Two-pass (stroke first, fill on top) - **required for OTF reliability** |
| Line height | 1.18x font size |
| Kerning | -1.0 |
| Position | Top of text at **y=440** on 1920-tall canvas (= 22.9% from top), centered horizontally |
| Internal PNG padding | `ceil(outlineWidth) + 8` → so PNG overlay y = 440 - 8 = **432** |
| Audio | Ripped via `ffmpeg -vn -c:a aac -b:a 192k` |
| Upscale | `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920` (no black bars) |
| Encoding | `libx264 -crf 18 -preset fast -pix_fmt yuv420p` |
| Audio encoding | AAC 192k stereo |
| Final remux | `ffmpeg -fflags +genpts+igndts -c copy -movflags +faststart` (strips edit list) |

## Stage 1: Download Source Reel

```bash
BATCH=$(date +%Y-%m-%d)
DIR="viral-reels/batch-${BATCH}"
mkdir -p "$DIR/final"
cd "$DIR"
yt-dlp -o "source.%(ext)s" --write-info-json "<IG_URL>"
# Produces: source.mp4 + source.info.json
```

**What this gives you:**
- `source.mp4` - the reel video
- `source.info.json` - metadata: uploader, title (often the IG caption), like_count, comment_count, description (= IG caption)

## Stage 2: Extract Audio + Probe

```bash
# Probe duration, dimensions, framerate
ffprobe -v error -show_entries format=duration,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate -of default=noprint_wrappers=0 source.mp4

# Rip audio (AAC 192k - matches what we'll re-encode anyway)
ffmpeg -y -i source.mp4 -vn -c:a aac -b:a 192k audio.m4a

# Extract first frame at full resolution (for OCR + visual reference)
ffmpeg -y -i source.mp4 -vf "fps=30,select='eq(n\,0)'" -frames:v 1 -q:v 1 source-frame.png
```

**Record in tracker:**
- `duration_s` - exact seconds (need this for clip trimming)
- `source_creator` - from `info.json["uploader"]`
- `source_likes` - from `info.json["like_count"]`
- `source_caption` - from `info.json["description"]`

## Stage 3: OCR the On-Screen Text

Use the `Read` tool on `source-frame.png`. Claude can read the text directly from the image. **Verify carefully** because viewers will see this text exactly:

- Get the verbatim text including punctuation
- Preserve line breaks as the original creator wrote them (line breaks change pacing/rhythm)
- Note the position (e.g., "upper third, centered")
- Note any styling oddities (mixed case, abbreviated words like "u r" instead of "you are")

Present it back to the user verbatim and ask: **"approve 1:1 or edit?"** Either is fine; sometimes you'll want a fresh hook for the same template.

Save the approved text in the tracker as `on_screen_text` with `||` separating lines (matches the format `render_text.swift` expects).

## Stage 4: Wait For B-Roll Clip

Ask the user for a B-roll clip path. Always suggest 3 picks from the existing `b-roll/` library first if it has files. Rank candidates by:

- **Thematic fit** with the on-screen text (e.g. "go to the gym" → gym/workout clip; "work hard" → desk/late-night clip; lifestyle hooks → travel/luxury clips)
- **Visual aesthetic match** with the source frame (night vs day, indoor vs outdoor, slow vs energetic)
- **Avoid recent reuse** - check tracker for `user_clip_source` on recent posts

**Probe the clip:**
```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt -of default=noprint_wrappers=0 "/path/to/clip.MP4"
```

**Quality check:** if dimensions are <720 wide, the clip was probably WhatsApp/iMessage compressed. Tell the user and offer to proceed (output will be soft) or wait for an uncompressed source.

**Trim to source duration:**

```bash
ffmpeg -y -ss 0 -i "<clip path>" -t <duration_s> -c:v libx264 -crf 18 -preset fast -pix_fmt yuv420p -an clip-trim-temp.mp4
ffmpeg -y -fflags +genpts+igndts -i clip-trim-temp.mp4 -c copy -movflags +faststart clip-trimmed.mp4
rm clip-trim-temp.mp4
```

**Default trim point is 0** (first N seconds). If the start of the clip isn't thematically right for the text, ask the user what start time to use.

## Stage 5: Render the Hook PNG

```bash
# Format text with || as line breaks (matches what was approved in stage 3)
TEXT="line one of the hook||line two||line three||line four"
cd viral-reels
swift render_text.swift "$TEXT" "InstagramSans-Bold" 50 5 "batch-${BATCH}/final/NN-hook.png"
# Returns: WIDTHxHEIGHT (e.g. 667x310)
```

The renderer:
- Auto-registers any TTF/OTF in `~/Library/Fonts`
- Renders fill + stroke as two passes (works for both OTF and TTF)
- Output is a transparent PNG sized to the text bounding box
- `NN` = clip number within the batch, two digits zero-padded

## Stage 6: Composite

```bash
HOOK_PNG="batch-${BATCH}/final/NN-hook.png"
HOOK_W=$(ffprobe -v error -show_entries stream=width -of csv=p=0 "$HOOK_PNG")
HOOK_X=$(( (1080 - HOOK_W) / 2 ))   # center horizontally
HOOK_Y=432                            # top of text at y=440 minus 8px PNG padding

ffmpeg -y \
  -i "batch-${BATCH}/clip-trimmed.mp4" \
  -loop 1 -i "$HOOK_PNG" \
  -i "batch-${BATCH}/audio.m4a" \
  -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];
    [bg][1:v]overlay=x=${HOOK_X}:y=${HOOK_Y}:shortest=1[v]
  " \
  -map "[v]" -map "2:a" \
  -c:v libx264 -crf 18 -preset fast -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -movflags +faststart -shortest \
  "batch-${BATCH}/final/NN-output-temp.mp4"

# Strip edit list (fixes black first frame)
ffmpeg -y -fflags +genpts+igndts -i "batch-${BATCH}/final/NN-output-temp.mp4" -c copy -movflags +faststart "batch-${BATCH}/final/NN-<slug>.mp4"
rm "batch-${BATCH}/final/NN-output-temp.mp4"
```

**Optional side-by-side for review:**

```bash
ffmpeg -y -i "batch-${BATCH}/source.mp4" -i "batch-${BATCH}/final/NN-<slug>.mp4" \
  -filter_complex "[0:v]scale=540:960[L];[1:v]scale=540:960[R];[L][R]hstack=inputs=2[v]" \
  -map "[v]" -map "0:a" \
  -c:v libx264 -crf 20 -preset fast -c:a aac -b:a 128k -movflags +faststart -shortest \
  "batch-${BATCH}/final/NN-comparison.mp4"

open "batch-${BATCH}/final/NN-<slug>.mp4" "batch-${BATCH}/final/NN-comparison.mp4"
```

## Stage 7: Caption + Schedule

Either upload the finished MP4 manually to Instagram, or use the optional scheduler (see scheduler.py).

**Caption defaults:** A simple `follow @your_handle` works fine, or write something thematic. Never copy the original creator's caption verbatim.

**Important:** Instagram's "trial reel" feature is the right tool here. Trial reels go to non-followers only, you get real performance data on cold audience, then promote the winners. If your scheduler supports it (Metricool does), default to `TRIAL_REEL` with `shareTrialAutomatically: false`.

## Stage 8: Monitor & Promote

Pull analytics from your scheduler or Instagram Insights. Track in `trial_views`, `trial_likes`, etc. If a remake outperforms the source's per-view engagement, promote it to a full post.

## Tracker Statuses

| Status | Meaning |
|--------|---------|
| `new` | Source URL recorded, nothing downloaded yet |
| `downloaded` | Source video + audio + frame extracted, OCR text proposed |
| `awaiting_clip` | Text approved, waiting for user to provide B-roll |
| `clip_provided` | Clip received and trimmed to source duration |
| `rendered` | Final composite rendered, awaiting review |
| `ready` | Approved, caption written, ready to schedule |
| `scheduled` | Scheduled, awaiting publish time |
| `trial` | Published as trial reel on IG, monitoring performance |
| `promoted` | Promoted from trial to full post |
| `archived` | Decided not to publish |

## Tracker Fields

**Identity & source:**
- `id` - `batch-date/clip-number` (e.g. `2026-04-28/01`)
- `batch`, `clip_number`
- `source_url`, `source_creator`, `source_likes`, `source_comments`, `source_caption`
- `duration_s` - source video duration (target trim length for our clip)

**Content:**
- `on_screen_text` - verbatim text rendered in the overlay (use `||` for line breaks)
- `style_notes` - position, alignment, anything non-default

**Pipeline paths:**
- `source_path`, `audio_path`, `source_frame_path`
- `user_clip_source` - original path for the user's B-roll
- `clip_trimmed_path`, `hook_png_path`, `final_path`

**Pipeline state:**
- `status`, `notes`

**Publishing:**
- `caption`, `metricool_post_id`, `scheduled_date`, `posted_date`, `trial_date`, `instagram_url`

**Performance:**
- `trial_views`, `trial_likes`, `trial_comments`, `trial_saves`, `trial_shares`
- `views`, `likes`, `comments`, `saves`, `shares` (post-promotion totals)

## Common Issues

### Clip is lower resolution than source
Likely WhatsApp/iMessage compressed. Output will be soft after upscale. Ask for AirDrop or Photos export of the original instead.

### Source aspect ratio isn't 9:16
Some reels are close-but-not-exact (e.g. 464:832 = 0.5577 vs 0.5625). The `force_original_aspect_ratio=increase,crop=1080:1920` filter handles this; it scales up and crops the overflow. No black bars.

### Black first frame
The edit-list strip remux fixes this. If it reappears, the strip step was skipped.

### Text PNG renders hollow (stroke only, no fill)
Old versions of `render_text.swift` used `strokeWidth: -N` which fails for some OTF fonts. Current version draws stroke + fill as separate passes. If this regresses, check the renderer hasn't been reverted.

### Font missing on first run
Run the install commands at the top of the setup guide. The renderer auto-registers from `~/Library/Fonts` but the font has to actually be there first.

### Source duration isn't a round number (e.g. 6.245s)
Trim to exact duration with `-t 6.245`. Final output may be 6.256s due to frame boundaries; that's fine, the audio defines length and ffmpeg's `-shortest` handles it.

## Working With This Pipeline

This pipeline is Claude Code-driven. Claude reads this SKILL.md and `tracker.json` at session start, then executes each step using normal tools (Read, Bash, etc.). The only "automated" piece is `render_text.swift`; everything else is just running commands and updating JSON.

**Each step has a built-in review point.** Don't auto-progress through stages. After each, surface the result and wait for go-ahead. The exception: stages 1-3 (download/extract/OCR) can run in one go since they're cheap and reversible.
````

---

## Artifact 3: render_text.swift

Save this as `viral-reels/render_text.swift`. This is the hook renderer. macOS only (uses AppKit). If you're on Linux/Windows, port to Pillow with similar logic:

```swift
// Renders text in IG Classic style: white fill + black outline.
// Renders fill and stroke as TWO separate passes for reliability across font formats (OTF/TTF).
// Usage: render_text.swift <text> <fontName> <fontSize> <outlinePx> <output>
import AppKit
import CoreText
import Foundation

// Auto-register any custom fonts in ~/Library/Fonts so we don't need a separate install step.
let fontDir = NSHomeDirectory() + "/Library/Fonts"
if let files = try? FileManager.default.contentsOfDirectory(atPath: fontDir) {
    for f in files where f.hasSuffix(".ttf") || f.hasSuffix(".otf") {
        let url = URL(fileURLWithPath: fontDir + "/" + f) as CFURL
        var err: Unmanaged<CFError>?
        _ = CTFontManagerRegisterFontsForURL(url, .process, &err)
    }
}

guard CommandLine.arguments.count == 6 else {
    print("usage: <text||with||newlines> <fontName> <fontSize> <outlinePx> <output>")
    exit(1)
}
let rawText = CommandLine.arguments[1].replacingOccurrences(of: "||", with: "\n")
let fontName = CommandLine.arguments[2]
let fontSize = CGFloat(Double(CommandLine.arguments[3])!)
let outlineWidth = CGFloat(Double(CommandLine.arguments[4])!)
let outputPath = CommandLine.arguments[5]

let font = NSFont(name: fontName, size: fontSize) ?? NSFont.boldSystemFont(ofSize: fontSize)

let para = NSMutableParagraphStyle()
para.alignment = .center
para.lineSpacing = 0
para.minimumLineHeight = fontSize * 1.18
para.maximumLineHeight = fontSize * 1.18

let baseAttrs: [NSAttributedString.Key: Any] = [
    .font: font,
    .paragraphStyle: para,
    .kern: -1.0,
]

let strokeAttrs = baseAttrs.merging([
    .foregroundColor: NSColor.black,
    .strokeColor: NSColor.black,
    .strokeWidth: outlineWidth * 2,  // POSITIVE = stroke only, no fill
] as [NSAttributedString.Key: Any]) { _, new in new }

let fillAttrs = baseAttrs.merging([
    .foregroundColor: NSColor.white,
    .strokeWidth: 0,
] as [NSAttributedString.Key: Any]) { _, new in new }

let strokeStr = NSAttributedString(string: rawText, attributes: strokeAttrs)
let fillStr = NSAttributedString(string: rawText, attributes: fillAttrs)

let bounds = fillStr.boundingRect(with: CGSize(width: 1080, height: 2000), options: [.usesLineFragmentOrigin, .usesFontLeading])
let pad: CGFloat = ceil(outlineWidth) + 8
let imgW = Int(ceil(bounds.width + 2 * pad))
let imgH = Int(ceil(bounds.height + 2 * pad))

let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: imgW, pixelsHigh: imgH,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
rep.size = NSSize(width: imgW, height: imgH)

NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSColor.clear.setFill()
NSRect(x: 0, y: 0, width: imgW, height: imgH).fill()
let drawRect = NSRect(x: pad, y: pad, width: CGFloat(imgW) - 2*pad, height: CGFloat(imgH) - 2*pad)
// Pass 1: stroke (drawn in black, behind fill)
strokeStr.draw(with: drawRect, options: [.usesLineFragmentOrigin, .usesFontLeading])
// Pass 2: fill (white, drawn on top)
fillStr.draw(with: drawRect, options: [.usesLineFragmentOrigin, .usesFontLeading])
NSGraphicsContext.restoreGraphicsState()

let png = rep.representation(using: .png, properties: [:])!
try! png.write(to: URL(fileURLWithPath: outputPath))
print("\(imgW)x\(imgH)")
```

---

## Artifact 4: tracker.json (Empty Template)

Save this as `viral-reels/tracker.json`. The pipeline adds clips here as you go:

```json
{
  "_schema": {
    "version": 1,
    "purpose": "Track viral reel remakes - source metadata, pipeline state, performance.",
    "statuses": [
      "new",
      "downloaded",
      "awaiting_clip",
      "clip_provided",
      "rendered",
      "ready",
      "scheduled",
      "trial",
      "promoted",
      "archived"
    ]
  },
  "render_recipe": {
    "comment": "These params are pixel-tuned. Don't change without re-validating against a known-good source.",
    "font_name": "InstagramSans-Bold",
    "font_size_pt": 50,
    "stroke_color": "#000000",
    "stroke_width_px": 5,
    "fill_color": "#FFFFFF",
    "line_height_factor": 1.18,
    "kern": -1.0,
    "text_top_y_on_1920": 440,
    "png_internal_padding": 8,
    "overlay_y": 432,
    "output_resolution": "1080x1920",
    "scale_filter": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
    "video_codec": "libx264 -crf 18 -preset fast -pix_fmt yuv420p",
    "audio_codec": "aac -b:a 192k",
    "post_remux": "ffmpeg -fflags +genpts+igndts -c copy -movflags +faststart"
  },
  "clips": []
}
```

---

## Artifact 5: scheduler.py (Optional)

If you want auto-scheduling, save this as `viral-reels/scheduler.py`. **This requires a Metricool account and API access.** Skip this artifact entirely if you prefer to upload manually to Instagram (or use Buffer, Later, etc.).

Link to Metricool: https://i.mtr.cool/omnifusion (this is an affiliate link and supports the channel)

Before using, create `viral-reels/accounts.json` with your Metricool credentials:

```json
{
  "user_id": "YOUR_METRICOOL_USER_ID",
  "blog_id": "YOUR_METRICOOL_BLOG_ID",
  "api_token": "YOUR_METRICOOL_API_TOKEN"
}
```

And configure the timezone + posting window at the top of the script (the defaults below are placeholders, edit for your local timezone and audience peak hours):

```python
#!/usr/bin/env python3
"""
Auto-scheduler for viral reels.

Schedules rendered reels into the next available slot in the configured
window with constraints: no same audio (source_url) or same B-roll on the
same posting session, no slot collisions on Metricool.

Usage:
  python3 scheduler.py schedule <tracker-id> [--caption TEXT] [--at ISO]
  python3 scheduler.py list [--days N] [--all]
"""

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
TRACKER = os.path.join(ROOT, "tracker.json")
ACCOUNTS = os.path.join(ROOT, "accounts.json")

# CONFIGURE THESE FOR YOUR LOCAL CONTEXT
TZ = "America/New_York"       # IANA timezone string for your scheduling window
TZ_OFFSET_HOURS = -5          # UTC offset of the above (used for "now" math, ignores DST)
DEFAULT_CAPTION = "follow @your_handle"
SLOT_MIN = 30                 # slot length in minutes
WINDOW_START_HOUR = 20        # local hour the posting window opens
NIGHT_HOURS = 5               # window length in whole hours
NIGHT_EXTRA_MIN = 30          # plus this many extra minutes (so 20:00 + 5h30 = 01:30)
LOOKAHEAD_DAYS = 14
MAX_PER_DAY = 5               # max posts per posting session


def now_local():
    return dt.datetime.utcnow() + dt.timedelta(hours=TZ_OFFSET_HOURS)


def load_creds():
    with open(ACCOUNTS) as f:
        return json.load(f)


def load_tracker():
    with open(TRACKER) as f:
        return json.load(f)


def save_tracker(data):
    with open(TRACKER, "w") as f:
        json.dump(data, f, indent=2)


def night_slots(date):
    """30-min slots from WINDOW_START_HOUR on <date> through the configured window end."""
    start = dt.datetime(date.year, date.month, date.day, WINDOW_START_HOUR, 0)
    end = start + dt.timedelta(hours=NIGHT_HOURS, minutes=NIGHT_EXTRA_MIN)
    slots = []
    cur = start
    while cur <= end:
        slots.append(cur)
        cur += dt.timedelta(minutes=SLOT_MIN)
    return slots


def session_date(slot_dt):
    """Map a slot datetime to its posting-session date.

    A session runs WINDOW_START_HOUR of day N through the window end (possibly
    after midnight). Post-midnight slots belong to the session that started
    the previous calendar day. Used for same-audio / same-B-roll / max-per-
    session checks so a midnight crossover doesn't dodge the rules.
    """
    if slot_dt.hour >= WINDOW_START_HOUR:
        return slot_dt.date()
    return slot_dt.date() - dt.timedelta(days=1)


def fetch_scheduled(creds, days=LOOKAHEAD_DAYS):
    today = dt.date.today()
    end = today + dt.timedelta(days=days)
    url = (
        f"https://app.metricool.com/api/v2/scheduler/posts"
        f"?userId={creds['user_id']}&blogId={creds['blog_id']}"
        f"&start={today.isoformat()}T00:00:00&end={end.isoformat()}T00:00:00"
    )
    req = urllib.request.Request(url)
    req.add_header("X-Mc-Auth", creds["api_token"])
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get("data", []) if isinstance(data, dict) else data


def parse_post_dt(post):
    pd = post.get("publicationDate", {})
    s = pd.get("dateTime") if isinstance(pd, dict) else pd
    if not s:
        return None
    return dt.datetime.fromisoformat(s.replace("Z", ""))


def find_slot(creds, tracker, src_url, broll):
    """Next available slot satisfying audio + B-roll same-session constraints."""
    posts = fetch_scheduled(creds, LOOKAHEAD_DAYS)
    pid_to_entry = {
        e["metricool_post_id"]: e
        for e in tracker["clips"]
        if e.get("metricool_post_id")
    }

    taken = set()
    day_src = {}
    day_broll = {}
    day_count = {}
    for p in posts:
        pdt = parse_post_dt(p)
        if not pdt:
            continue
        taken.add(pdt.replace(second=0, microsecond=0))
        sd = session_date(pdt)
        day_count[sd] = day_count.get(sd, 0) + 1
        e = pid_to_entry.get(p.get("id"))
        if e:
            if e.get("source_url"):
                day_src.setdefault(sd, set()).add(e["source_url"])
            if e.get("user_clip_source"):
                day_broll.setdefault(sd, set()).add(e["user_clip_source"])

    now = now_local()
    for day_off in range(0, LOOKAHEAD_DAYS + 1):
        cand_date = now.date() + dt.timedelta(days=day_off)
        for slot in night_slots(cand_date):
            if slot < now + dt.timedelta(minutes=15):
                continue
            sd = session_date(slot)
            if day_count.get(sd, 0) >= MAX_PER_DAY:
                continue
            if src_url and src_url in day_src.get(sd, set()):
                continue
            if broll and broll in day_broll.get(sd, set()):
                continue
            if slot.replace(second=0, microsecond=0) in taken:
                continue
            return slot
    return None


def upload_tmpfiles(file_path):
    res = subprocess.run(
        ["curl", "-s", "-F", f"file=@{file_path}",
         "https://tmpfiles.org/api/v1/upload"],
        capture_output=True, text=True, check=True
    )
    d = json.loads(res.stdout)
    return d["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")


def schedule_metricool(creds, video_url, caption, when):
    body = {
        "text": caption,
        "publicationDate": {
            "dateTime": when.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": TZ,
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
    }
    api = (
        f"https://app.metricool.com/api/v2/scheduler/posts"
        f"?userId={creds['user_id']}&blogId={creds['blog_id']}"
    )
    req = urllib.request.Request(api, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Mc-Auth", creds["api_token"])
    with urllib.request.urlopen(req) as resp:
        r = json.loads(resp.read())
    return r.get("data", {}).get("id") if isinstance(r.get("data"), dict) else r.get("id")


def cmd_schedule(args):
    tracker = load_tracker()
    entry = next((e for e in tracker["clips"] if e["id"] == args.id), None)
    if not entry:
        sys.exit(f"ERROR: id {args.id} not in tracker")
    if entry["status"] not in ("rendered", "ready"):
        sys.exit(f"ERROR: status is '{entry['status']}' (expected rendered/ready)")
    if not entry.get("final_path"):
        sys.exit("ERROR: no final_path on entry")

    final = os.path.join(ROOT, entry["final_path"])
    if not os.path.exists(final):
        sys.exit(f"ERROR: missing file: {final}")

    creds = load_creds()
    if args.at:
        slot = dt.datetime.fromisoformat(args.at)
        print(f"Forced slot: {slot.strftime('%a %Y-%m-%d %H:%M')} {TZ}")
    else:
        slot = find_slot(creds, tracker, entry.get("source_url"), entry.get("user_clip_source"))
        if not slot:
            sys.exit(f"ERROR: no available slot in next {LOOKAHEAD_DAYS} days")
        print(f"Next slot: {slot.strftime('%a %Y-%m-%d %H:%M')} {TZ}")

    size_mb = os.path.getsize(final) / 1024 / 1024
    print(f"Uploading {os.path.basename(final)} ({size_mb:.1f} MB)...")
    url = upload_tmpfiles(final)
    print(f"  {url}")

    caption = args.caption or entry.get("caption") or DEFAULT_CAPTION
    print(f"Caption: {caption}")
    print("Scheduling on Metricool...")
    pid = schedule_metricool(creds, url, caption, slot)
    if not pid:
        sys.exit("ERROR: schedule returned no post ID")
    print(f"  Post ID: {pid}")

    entry["status"] = "scheduled"
    entry["caption"] = caption
    entry["metricool_post_id"] = pid
    entry["scheduled_date"] = slot.strftime("%Y-%m-%d %H:%M")
    save_tracker(tracker)
    print(f"\nDone. Tracker updated for {entry['id']}.")


def cmd_list(args):
    creds = load_creds()
    tracker = load_tracker()
    posts = fetch_scheduled(creds, args.days)
    pid_to_entry = {
        e["metricool_post_id"]: e
        for e in tracker["clips"]
        if e.get("metricool_post_id")
    }

    posts_by_slot = {}
    for p in posts:
        pdt = parse_post_dt(p)
        if pdt:
            posts_by_slot[pdt.replace(second=0, microsecond=0)] = p

    today = now_local().date()
    print(f"Schedule next {args.days} days (window: {WINDOW_START_HOUR:02d}:00 + {NIGHT_HOURS}h{NIGHT_EXTRA_MIN}m {TZ}, {SLOT_MIN}-min slots)\n")
    print(f"{'Slot':<22} {'Status':<8} {'Source':<18} B-roll")
    print("-" * 80)

    used = 0
    total = 0
    for off in range(args.days):
        d = today + dt.timedelta(days=off)
        slots = night_slots(d)
        for slot in slots:
            total += 1
            key = slot.replace(second=0, microsecond=0)
            tag = "open"
            src = ""
            broll = ""
            if key in posts_by_slot:
                used += 1
                tag = "TAKEN"
                p = posts_by_slot[key]
                e = pid_to_entry.get(p.get("id"))
                if e:
                    src = (e.get("source_creator") or "?")[:16]
                    bp = e.get("user_clip_source") or ""
                    broll = bp.replace("b-roll/", "").rsplit(".", 1)[0][:30]
                else:
                    src = "(orphan)"
            if tag == "TAKEN" or args.all:
                print(f"{slot.strftime('%a %m/%d %H:%M'):<22} {tag:<8} {src:<18} {broll}")
        if args.all:
            print()

    print(f"\n{used}/{total} slots used in next {args.days} days "
          f"({total - used} open)")


def main():
    ap = argparse.ArgumentParser(description="Auto-scheduler for viral reels")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schedule", help="Schedule a rendered reel")
    s.add_argument("id", help="Tracker entry id (e.g. 2026-04-29/01)")
    s.add_argument("--caption", help="Override caption")
    s.add_argument("--at", help="Force specific datetime (ISO format, local time naive)")
    s.set_defaults(func=cmd_schedule)

    s = sub.add_parser("list", help="Show schedule overview")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--all", action="store_true", help="Show all slots, not just taken")
    s.set_defaults(func=cmd_list)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

---

## How To Use It

Once setup is done, your day-to-day flow is just three commands:

### 1. Find a viral reel you want to remake

Look for the format: B-roll + trending audio + one static text block. Aspirational/lifestyle stuff with high view counts and decent like ratios. Save the IG URL.

### 2. Send it to Claude

```
/viral-reels new https://www.instagram.com/p/ABC123/
```

Claude downloads the reel, rips the audio, extracts a frame, reads the on-screen text, and asks you:
- "Approve the OCR'd text 1:1 or want to edit?"
- "Which B-roll clip should we use?"

### 3. Provide a clip and let it render

```
/viral-reels remake 2026-05-01/01 --clip ~/Downloads/my-clip.mp4
```

Claude trims your clip to source duration, renders the hook PNG, composites everything, and shows you a side-by-side comparison with the source. Approve the output, then either:

- **Manual:** Open the file in `viral-reels/batch-YYYY-MM-DD/final/`, upload directly to Instagram as a trial reel
- **Automated:** Run `python3 viral-reels/scheduler.py schedule 2026-05-01/01` to schedule via Metricool

Link to Metricool: https://i.mtr.cool/omnifusion (this is an affiliate link and supports the channel)

---

## What's Special About This Setup

**The pixel-tuned render recipe.** Most "make viral reels" tutorials hand-wave the production. The numbers in this pipeline (font size 50pt, position y=440, stroke 5px, line height 1.18x, kerning -1.0) were tuned by overlaying renders on real Instagram screenshots until they were indistinguishable from organic IG text. Match the format and the format does the heavy lifting.

**Two-pass stroke + fill rendering.** Most text renderers use a single pass with `strokeWidth: -N` for outline + fill. This breaks silently on many OTF fonts and you get hollow text. Drawing the stroke and the fill as two separate `NSAttributedString.draw()` passes is bulletproof across font formats.

**The edit list re-mux.** That mysterious black frame at the start of every H.264 export comes from the encoder delay edit list. One extra ffmpeg pass with `-fflags +genpts+igndts -c copy` strips it. Without this, every reel opens with a black flash that hurts retention.

**1x bitmap rendering instead of NSImage.** `NSBitmapImageRep` directly with `NSGraphicsContext` gives you exact pixel dimensions. NSImage on Retina silently doubles your output. The 1x trick keeps the PNG at the size you asked for.

**Ripped audio, never replaced.** The whole point of remaking a viral reel is using the same trending audio. People scroll past 1000 reels a day; the audio is the hook. If you replace the audio, you're not remaking the reel, you're just making a new reel that uses someone else's text.

**Trial reels first.** Instagram's trial reel feature shows the post only to non-followers, gives you raw performance data on cold audience, and lets you promote winners while quietly archiving flops. This is the only sane way to ship volume without burning your own audience on misses.

**Session-aware scheduling (not calendar-day).** Two posts at 21:00 Thursday and 00:30 Friday are 3.5 hours apart but on different calendar dates. The algorithm doesn't care about midnight rollover, it cares about real-time proximity. The scheduler maps slots to "posting sessions" (window-start through window-end across midnight) so same-audio and same-B-roll constraints behave correctly.

---

## Customization Notes

**Font.** Instagram Sans Bold is what IG natively uses, which is why this format blends in. If you want a different look, swap the font name in `render_text.swift` invocations. The render recipe values (size, line height, kerning) are tuned for Instagram Sans Bold; if you change the font, re-validate by overlaying on a known-good source.

**Hook position.** y=440 on a 1920 canvas is upper-third, where most IG reel text sits. If your style is bottom-third or center, change `HOOK_Y` in the composite step (and adjust by the PNG padding offset).

**Scheduler.** This guide includes Metricool because it has trial reel API support. If you use Buffer, Later, or post manually, ignore the scheduler entirely. The pipeline output is a finished MP4 either way.

Link to Metricool: https://i.mtr.cool/omnifusion (this is an affiliate link and supports the channel)

**Posting window.** Defaults in the scheduler are a 20:00 to 01:30 evening window in a placeholder IANA timezone. Edit `WINDOW_START_HOUR`, `NIGHT_HOURS`, `NIGHT_EXTRA_MIN`, `TZ`, and `TZ_OFFSET_HOURS` at the top of scheduler.py for your audience's peak hours and your local timezone.

**Captions.** The default caption is just a follow CTA. For higher engagement, write a 1-2 line caption that complements the on-screen text. Don't copy the original creator's caption verbatim. That's lazy and the algo notices.

**B-roll library.** Build up a folder of 20-30 reusable clips in `viral-reels/b-roll/`. Common categories: gym, desk/work, travel, food, car, lifestyle moments. The pipeline gets faster the more you have, because Claude can suggest fits from the library instead of waiting for new clips.

---

## License + Credit

This is a free resource. Take it, adapt it, ship it. If you build something cool with it, no need to credit, but a shoutout is always nice.

Have fun building.
