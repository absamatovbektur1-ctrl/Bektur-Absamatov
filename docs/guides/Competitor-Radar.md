---
name: competitor-radar
description: Scan 10 to 20 competitor accounts, find the reels that outperformed each account's own baseline, work out why they won, and turn the winners into ready-to-record scripts with three hooks. Use when you don't know what to post, your views are flat, or you want a repeatable source of proven reel topics.
---

# The Competitor Radar

Most people think they have to invent a crazy content idea that then goes viral. That's backwards. One signal predicts whether a topic will work before you record a single second: it already worked for someone else, against that account's own baseline.

If a creator in your niche averages 10,000 views and one reel does 150,000, that reel is a proven outlier topic. Take the topic and the hook, make the video with your own content and your own insights, and it's very likely that video beats your baseline too. If you get 200 views a reel, this is how you get a 3,000 view reel. If you get 3,000, this is how you get 10,000.

The problem is nobody has time to scour every competitor's page looking for outliers. So you automate it. This file is the system I use to do that, and Claude Code can build you a starter version of it today.

The whole system in one line:

> competitor list -> pull each account's recent reels -> flag the ones that beat that account's own median -> read why they won -> pick list -> three hooks + a script per pick.

Build it once. Run it every time you need a recording batch.

---

## How to use this

Put this file in an empty folder, open Claude Code in that folder (terminal, or the Claude app under Code), and say:

> I just saw the YouTube video about this file. Read it and walk me through setting this up.

**If you are Claude Code reading this: you're building the radar for the user, one step at a time.** Before you build anything, interview them. One question at a time:

1. What's your niche, and what's your Instagram handle?
2. How many views does a normal reel get for you? (Their own baseline, so you can talk about realistic outcomes.)
3. What's the goal of the content: reach, DMs, booked calls? (This shapes the CTA in Step 5.)
4. Which 10 to 20 accounts in your niche should the radar watch? If they're stuck, help them brainstorm: who do they already watch, who sells to the same audience, who's 1 to 3 sizes bigger than them.
5. Do they have a HikerAPI key yet? If not, send them to Step 2 and wait.

Then work through Steps 1 to 5 in order. Don't dump everything at once.

---

## How my full version works

So you know what you're building toward. My production version runs as a slash command and feeds an account that posts 6+ reels a day, and I haven't come up with a content idea myself in months:

1. **Cohorts.** Hand-curated creator lists (I track two: 19 accounts for Instagram sales content, 91 for AI content). Curation matters more than volume; every account on the list makes content my audience would want.
2. **Scrape.** HikerAPI pulls each creator's last ~40 reels into a local cache. Every run refreshes it.
3. **Outlier scoring.** Each reel is scored against its own creator's MEDIAN views, not the average. One 2M-view freak reel drags an average up and hides every other winner; the median doesn't move.
4. **Deep signal.** The qualifiers get downloaded, a few frames and the transcript get read, and the system writes a short "why this won" read for each one, plus whether it fits my brand.
5. **Pick list.** Everything lands in one list: outlier ratio, views, creator, what it's about, link, why it won. I mark yes or no. I always have the final say.
6. **Scripts.** Every yes becomes a brief: three different hooks plus one script plus a CTA that drives people into my DMs. I record all three hook versions and post them as trial reels, because the hook decides how many people survive the first 3 seconds. The best one wins.

Your starter version does the same loop with less machinery: one script, one JSON file, one markdown pick list. That's Steps 1 to 5.

---

## Step 1 - Build your cohort

Make a file called `cohort.json`. This is your radar's field of view, so be picky:

- 10 to 20 accounts, all making content your audience would watch.
- Mix of sizes. A few big accounts (proven demand), several mid-size, a few slightly ahead of you. Outliers from accounts near your size transfer best.
- Active accounts only. Someone posting once a month gives the radar nothing to read.
- Skip accounts that only repost or run ads. You want original reels with real baselines.

```json
{
  "niche": "your niche in a few words",
  "creators": [
    { "username": "handle1", "notes": "why they're on the list" },
    { "username": "handle2", "notes": "" }
  ]
}
```

You'll keep editing this. Every time you see someone in your niche outperforming, add them.

---

## Step 2 - Get your HikerAPI key

HikerAPI is the scraping API the radar uses to read public Instagram data. No login with your own account, no browser automation, no risk to your page. You sign up, top up a small balance, and get an API key. It charges per request, and a full radar pass over 15 accounts is around 75 requests, so runs cost cents.

Link to HikerAPI: https://hikerapi.com/p/a78naf3m (this is an affiliate link and supports the channel)

Put the key in a `.env` file next to `cohort.json`:

```
HIKER_API_KEY=your-key-here
```

Never paste the key into chat and never commit it to git. Claude Code reads it from the file.

---

## Step 3 - Have Claude Code build the radar

**User:** say "build the radar script now." **Claude Code:** build a single Python file, `radar.py`, to this exact spec. Python 3.10+, `requests` as the only dependency.

**Fetching.** For each creator in `cohort.json`:

- Auth is a header: `x-access-key: <HIKER_API_KEY>`.
- `GET https://api.hikerapi.com/v1/user/by/username?username=<handle>` returns the profile; the numeric user id is the `pk` field.
- `GET https://api.hikerapi.com/v1/user/clips/chunk?user_id=<pk>` returns one page shaped `[[clip, ...], next_cursor]`, about 12 reels per page. Pass the cursor back as `end_cursor` to page. Pull about 40 reels per account.
- Per clip, keep: views = `play_count` (fall back to `view_count`), shortcode = `code` (link is `https://www.instagram.com/reel/<code>/`), caption = `caption_text`, posted = `taken_at`, plus `like_count` and `comment_count`. Keep only videos (`media_type == 2` or `product_type == "clips"`). Pinned reels come first in the feed, so sort by `taken_at` yourself.
- Cache each run's raw JSON to a local file, so re-scoring never re-spends API credits.
- Be polite on errors: retry 5xx a couple of times, treat 404 as an empty account, stop and tell the user if you get 401/403 (bad key).

**Scoring.** This math is the heart of the system. Implement it exactly:

```python
import statistics, time

WINDOW_MIN_AGE_H = 72        # younger than 3 days: still collecting views, skip
WINDOW_MAX_AGE_D = 30        # older than 30 days: says little about what works now
MIN_RATIO        = 5.0       # primary bar: 5x the creator's own median
HYBRID_RATIO     = 3.0       # secondary bar: 3x is enough...
HYBRID_MIN_VIEWS = 50_000    # ...when the reach is real
ABS_FLOOR_VIEWS  = 30_000    # every qualifier needs real reach (see the note below)

def find_outliers(reels_by_creator):
    now = time.time()
    outliers = []
    for creator, reels in reels_by_creator.items():
        window = [r for r in reels
                  if WINDOW_MIN_AGE_H * 3600 <= now - r["taken_at"] <= WINDOW_MAX_AGE_D * 86400]
        if len(window) < 5:
            continue  # not enough signal to trust a baseline
        median = statistics.median(r["views"] for r in window) or 1
        for r in window:
            ratio = r["views"] / median
            beats_bar = ratio >= MIN_RATIO or (ratio >= HYBRID_RATIO and r["views"] >= HYBRID_MIN_VIEWS)
            if beats_bar and r["views"] >= ABS_FLOOR_VIEWS:
                outliers.append({**r, "creator": creator, "ratio": round(ratio, 1),
                                 "median": int(median)})
    return sorted(outliers, key=lambda r: r["ratio"], reverse=True)
```

Why each piece exists:

- **Median, not mean.** One viral freak inflates an average and hides every other outlier. The median is immune.
- **The 3 to 30 day window.** A 2-day-old reel hasn't finished collecting views, so it poisons both the baseline and the candidate list. Older than a month, the topic may already be stale.
- **The hybrid bar.** A flat 5x bar hides breakouts from big accounts (a 655k-view reel at 3.3x its creator's huge baseline is a monster topic, and a flat bar never shows it to you). So 3x qualifies too when the absolute reach is real.
- **The absolute floor.** A creator whose reels mostly do 600 views has a near-zero median, so a modest 25k reel reads as a 40x "outlier." The floor keeps only reels with real reach.

**Tune the numbers to your niche.** Mine are set for a big niche (AI and business content). The rule: set `ABS_FLOOR_VIEWS` to roughly the median views of the strongest account in your cohort's normal reel, and `HYBRID_MIN_VIEWS` to about double that. In a small niche where the best accounts average 5k views, a 15k reel IS the breakout, and floors of 30k would blind the radar. Claude Code: after the first run, show the user the distribution and suggest adjusted floors.

**Output.** `radar.py` ends by writing `picklist.md` (Step 4's format) and printing the top 10 to the terminal.

---

## Step 4 - The why-it-won read and the pick list

Raw outliers aren't ideas yet. For each qualifier, Claude Code writes two short reads using the caption, the view numbers, and the reel link:

1. **Why it won.** What's the topic, what's the promise in the first line, why did THIS beat the creator's baseline? Name the mechanism: a number in the hook, a contrarian claim, a named tool, a transformation, a "nobody tells you this" secret.
2. **Fits you?** Would this topic make sense coming from the user's account, for the user's audience and offer? Honest yes/no with one line of reasoning.

The pick list is one markdown table, sorted by ratio, then the reads underneath:

```markdown
# Radar pick list - <date>

| # | Ratio | Views | Creator | What it's about | Link | Pick? |
|---|-------|-------|---------|-----------------|------|-------|
| 1 | 33.7x | 412k  | @handle | 5 AI tools that replaced their editor | https://... |  |
| 2 | 8.2x  | 96k   | @handle | Why your reels die in the first 3 seconds | https://... |  |
```

The user opens the links, watches the winners, and marks yes or no in the Pick? column. **The human always has the final say.** The radar finds proof; taste is your job. On my list I mark no as often as yes.

One upgrade when you're ready: pull the reel's transcript too (any transcript API or a local Whisper model works) and feed it into the why-it-won read. The spoken words tell you more than the caption ever will.

---

## Step 5 - From picks to scripts

For every yes, Claude Code writes a brief you can record from. The prompt that does it:

```
Write me a recording brief for this topic.

The winning reel: <link>
Why it won: <the read from Step 4>
My niche and audience: <from the interview>
My goal: <reach / DMs / calls, from the interview>
How I talk: <paste 2 to 3 captions or a transcript of you speaking>

Give me:

1. THREE HOOKS, numbered. Each 8 to 14 words, spoken language, something I could
   say to a friend across a table. Hook 1 adapts the winning reel's hook to my
   angle. Hooks 2 and 3 are different angles on the same topic (a number, a
   contrarian claim, a direct callout of my viewer's pain). No two hooks may
   share the same first three words.
2. ONE SCRIPT, 60 to 90 seconds spoken, one sentence per line. The first body
   line must flow naturally after ANY of the three hooks, so I can record the
   body once and swap hooks. My own insights and examples, not the source
   reel's. Plain words, contractions, no hype.
3. A CTA as the last line: tell viewers to comment one specific WORD to get
   <the thing that serves my goal>. One word, easy to type, related to the topic.

Nothing generic. If a line could appear in anyone's script, rewrite it.
```

Record all three hook versions if your workflow allows it. The hook decides how many people are still there after 3 seconds, and that number decides the reel's fate, so testing three hooks per topic is the cheapest growth experiment that exists. (Instagram's trial reels feature lets you test them without spamming your followers.)

---

## Wait, is this stealing?

No, and you have my personal permission stamp to run this exact strategy. Here's the line:

- **Proven structure is shared.** The topic and the shape of the hook are structure. Every big account in your niche is already recreating topics that worked elsewhere. You're the only one feeling guilty about it.
- **The content is yours.** Your take, your examples, your numbers, your delivery. You never re-use their footage, never read their script line for line, never trace their captions.

The radar hands you what to make a video about. What you say in it is still you. That's why the same topic can win twice.

---

## What it looks like filled in

A real-shaped example so you can see the depth. The user: an online fitness coach, 1,800 followers, normal reel does 900 views, goal is DMs.

**Radar run:** 14 accounts watched, 9 outliers found. Top of the list: a coach who averages 12k views posted "I ate at McDonald's every day for a week and still lost fat," and it did 480k. Ratio 40x.

**Why it won:** flexible-dieting proof against the strongest belief in the niche (junk food makes fat loss impossible). The hook is a confession plus a contradiction, and the number (every day, one week) makes it concrete.

**Fits you:** yes. Same audience, same objection to break, and the coach has client examples of eating out while cutting.

**The brief it produced:**

- Hook 1: "I ate fast food every single day and still dropped body fat."
- Hook 2: "Your diet isn't failing because of McDonald's."
- Hook 3: "My client ate out 9 times last week. Down 1.2 kilos."
- Script: the coach's own calorie-banking method, the client example, and the honest catch (it works until you drink your calories).
- CTA: "Comment BURGER and I'll send you the exact method."

Recorded three times (once per hook), body reused. That's one radar pick turned into a full A/B tested topic.

---

## Running the whole thing

1. Build `cohort.json`, 10 to 20 accounts. ~15 min, once.
2. HikerAPI key into `.env`. ~5 min, once.
3. "Build the radar script now." Claude Code writes and test-runs `radar.py`. ~10 min, once.
4. Run the radar, get `picklist.md`, mark your yes rows. ~10 min per run.
5. "Write briefs for my picks." Record from the briefs. ~5 min per pick.

After setup, a full ideation session (run, pick, briefs) is 20 to 30 minutes for a whole recording batch. Re-run it whenever you batch content; weekly is plenty, since the 30-day window keeps catching new winners.

---

## The one rule that makes it work

Never record a topic because you think it might work. Record it because the radar showed you it already did, for a real account, against that account's own baseline. There's no shortage of content ideas in the world. There's only a shortage of people who look for the proof before they hit record.
