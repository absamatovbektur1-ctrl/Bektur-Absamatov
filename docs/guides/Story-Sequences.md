---
name: story-sequences
description: Build an automated Instagram Story sequence engine with Claude Code. Two proven sequence types, native-looking frame design rules, a specific-keyword CTA formula, and a deterministic renderer that turns one idea into 5-7 ready-to-post 1080x1920 story frames. Use when followers aren't turning into DM conversations, or when story posting keeps falling off your calendar.
---

# Automated Instagram Story Sequences

Reels and posts win you strangers. Stories are where followers turn into DM conversations, and DM conversations are where the money is. Almost nobody posts story sequences consistently because making them by hand is slow: come up with an idea, design every frame, add proof, and watch it all disappear after 24 hours.

This file fixes that. It contains the full content framework (the two sequence types, the frame design rules, the CTA formula) plus a build spec your Claude Code can implement. The result is a system where you speak or type one idea and get back a complete, native-looking story sequence as rendered 1080x1920 frames, ready to post or schedule.

The whole system in one line:

> idea (one sentence) -> Claude writes the sequence as a config file -> a renderer draws the frames -> you tweak for 5 minutes -> post or schedule.

This is the technical blueprint plus the framework. Personal identifiers, brand handles, account IDs, and client data have been stripped so you can adapt everything to your own brand.

---

## How to use this

Two ways, pick one:

1. **As a Claude Code skill (recommended).** Save this file as `.claude/skills/story-sequences/SKILL.md` inside a project folder. Then tell Claude Code: "use the story-sequences skill and build the system." It has everything it needs: the framework, the schema, the renderer spec, and the build prompt.
2. **Framework only.** If you don't want to build anything yet, skip Part 2 and use Part 1 as your manual playbook: write the frames yourself in Canva or Figma following the structures, design rules, and CTA formula. The framework works by hand too, it's just slower.

The build takes one session (Claude Code does the coding, you review the test renders). After that, every new sequence is about 10 minutes of your time.

---

## Why story sequences

Picture this. Somebody sees one of your reels, enjoys it, and follows you. If you pitch them now, there's no trust. They've seen a couple of minutes of your content at most.

Story sequences close that gap. Posted at least twice a week, they do two jobs:

- **Build authority.** Show your followers you know what you're talking about: insights, proof, results, the work behind the results.
- **Create an easy next step.** End some sequences with a specific call to action that pulls people into your DMs, where you can actually have a conversation and book calls.

Someone who watches your stories for weeks positions you as the expert in their head. When the right CTA lands, they reply, and the DM conversation starts warm instead of cold. That's the entire play: reach content wins the follower, story sequences turn the follower into a lead.

The reason to automate it isn't laziness. It's that consistency is the whole mechanism, and nobody sustains twice-a-week hand-designed sequences for months. A system does.

---

## Part 1 - The framework

### The two sequence types

Every sequence you post is one of two types. Nothing else.

1. **Authority** (no ask). Builds credibility and lets it marinate. No CTA, no link, nothing to reply to. These are what make the CTA sequences work. Post them, don't ask for anything.
2. **Authority + CTA**. The same authority build, but it earns an ask and ends in a specific-keyword call to action that drops the viewer into your DMs.

Rhythm: roughly 2 authority sequences for every 1 CTA sequence. If every sequence asks, none of them land.

### The structures

Both types are 5 to 7 frames. Each frame is one beat with one job.

**Authority:**

| Frame | Role | What it does |
|---|---|---|
| 1 | hook | Grab attention with one of the hook patterns below |
| 2-3 | context | What you're working on, what's happening with clients. Set the scene |
| 4-5 | proof | Stack the wins: results, before/after, real numbers. Overlay a real screenshot if you have one |
| 6 | lifestyle | The person behind the work: the desk, the process, why you do it |
| 7 | optional | An engagement frame, usually with a native poll sticker |

**Authority + CTA:**

| Frame | Role | What it does |
|---|---|---|
| 1 | hook | Grab attention |
| 2-3 | authority | Teach a concept or show results. Earn the right to pitch |
| 4-5 | credibility | Stack proof: client wins, your experience, why your method works |
| 6 | bridge | Frame the viewer's problem. Make them feel the gap your resource fills |
| 7 | cta | The specific-CTA formula (below), plus a link sticker if you have a resource page |

Drop a frame for a tighter set, but every sequence needs at least one hook, one proof beat, and one human beat, and a CTA sequence always ends on the formula.

### Hook patterns

Frame 1 decides whether anyone taps through. Pick one pattern per sequence:

- **Basic-use vs whole-system (the strong default).** Name the small way most people use a tool, then the full system you run with it. "Most people use AI to write captions. I use it to run my entire content system, from ideas to posting."
- **Bold stat.** "3 clients hit their best month this quarter. Here's what we did differently."
- **Hot take.** "You don't need a bigger team. You need one system that runs the busywork."
- **Result flex.** "Just got this message from a client. 11 sales calls booked while he was asleep."
- **Pattern interrupt.** "Most people automate the wrong thing first. Here's the order that actually works."

Bad hooks: a random selfie, a good-morning coffee photo, a result screenshot with no follow-through. A hook opens a loop the rest of the sequence closes.

### The CTA formula

The final frame of an authority + CTA sequence follows this shape, verbatim:

> "If you [specific situation], reply with [KEYWORD] and I will send you [specific thing]."

Example: "If you're a coach who wants clients checking in without you chasing them, reply with PLAN and I will send you the exact template my clients use."

Rules that make it convert:

- **Specific, never "DM me if interested."** Name the situation and name the thing they get.
- **The keyword is one uppercase word**, unique and memorable. PLAN, SYSTEM, TEMPLATE.
- **One keyword per running CTA.** If a reel CTA and a story CTA use the same keyword at the same time, your DM automation can't tell them apart. Keep a list.
- The reply is the point. A reply opens the DM thread, which is where the conversation (and the booking) happens.

### The design rules

These rules are what make frames look native instead of like ads. They're also exactly what the renderer in Part 2 enforces.

- **A real photo on every frame.** You at the desk, the screen, the whiteboard, the gym, the lifestyle. Color-graded to pop (rich, contrasty, slightly darker) under a dark gradient that darkens only where the text sits, so the rest of the photo breathes. Never a plain colored background, never a generated graphic.
- **Text sits high.** Default the text block to the top of the frame with the photo breathing below it. It reads instantly with the thumb hovering.
- **2-3 short lines per frame.** A big headline plus 1-2 smaller supporting lines. One idea per line. A whole frame reads in under 3 seconds.
- **One marker underline, max.** A single continuous marker line under the one phrase that matters on the frame (the claim, the proof number, the keyword). Pick ONE accent color that fits your brand and use it for every highlight in every sequence, never a mix. Many frames have zero highlights. This restraint is the signature.
- **Photo pairs.** Each background photo carries two frames: a setup beat, then a payoff beat on the same photo where the setup text stays visible but dimmed and the new line lands bright below it. The sequence steps forward photo by photo, two taps each. A photo may stand alone for a single-tap beat; never stack more than 3 beats on one photo.
- **Proof is a real screenshot or nothing.** A client message, a dashboard, a payment notification, composited as a small rounded card with a shadow. Crop to just the message bubble, blur names and faces. Never draw a fake proof graphic.

### The voice rules

Give these to Claude along with 3-5 samples of how you actually write (captions, DMs, a transcribed voice note):

- Short, complete sentences. One idea per sentence. It should read spoken, not written.
- Specific numbers beat vague claims. "40 hours down to 4," not "saves tons of time."
- Sentence case. No hashtags, no emojis, no em dashes.
- No hype words: unlock, elevate, game-changer, seamless, supercharge, "dive in."
- Honest, not hyped. Don't promise the dream, show the work.

---

## Part 2 - The build

This is the part you hand to Claude Code. The system is deliberately simple: one config file per sequence (written by Claude), one deterministic Python renderer (written once, no AI at render time), and a folder of your own photos and proof screenshots that both draw from.

Why a deterministic renderer instead of having AI generate images: your frames come out consistent, editable, and instant. Change one word in the config, re-render, done. No prompt roulette, no six-finger hands, and the photos are actually you.

### Folder layout

```
story-sequences/
  render.py                  # the renderer (Claude Code writes this from the spec below)
  prompts/
    generate.md              # the generation prompt (Part 3, saved so Claude can re-read it)
  assets/
    backgrounds/             # your photo library, self-described by INDEX.md
      INDEX.md
    testimonials/            # cropped, blurred proof screenshots + INDEX.md
      INDEX.md
    fonts/                   # a bold sans-serif family (free on Google Fonts)
  sequences/
    <slug>/
      config.json            # the sequence definition (Claude writes this per idea)
      sources/               # photos used by this sequence (copied in at render time)
      results/               # proof screenshots used by this sequence
      frame_1.png ... frame_N.png
      post-order.md          # the posting checklist the renderer emits
```

### The config schema

One JSON file fully describes a sequence. This is the contract between the generation step and the renderer:

```json
{
  "slug": "kebab-case-from-the-topic",
  "type": "authority",
  "keyword": null,
  "highlight_title": "short title for the IG Highlight cover",
  "profile": { "handle": "@yourhandle" },
  "frames": [
    {
      "n": 1,
      "role": "hook",
      "blocks": [
        { "text": "the headline, the punchy first line" },
        { "text": "a supporting line that adds the detail",
          "highlights": [ { "text": "key phrase", "style": "underline" } ],
          "size": "med" }
      ],
      "background": { "type": "photo", "src": "desk-late-night.jpg", "zoom": 1.0, "focus": "center" },
      "screenshot": null,
      "screenshot_pos": null,
      "text_position": "top",
      "sticker": null
    },
    {
      "n": 2,
      "role": "hook",
      "continues": true,
      "blocks": [ { "text": "the turn, landing bright below the dimmed setup text" } ],
      "screenshot": null,
      "sticker": null
    }
  ]
}
```

Validation rules (the renderer should enforce these in a `--validate` mode and refuse to render a config that breaks them):

- `type` is `authority` or `authority_cta`. `keyword` is `null` for authority, one unique UPPERCASE word for authority_cta.
- 5-7 frames, `n` 1-based and sequential.
- Each frame has 1-3 `blocks`. The first block is the headline (rendered big), the rest are supporting lines (rendered smaller). Optional per-block `size` in {big, med, small}.
- At most ONE highlight per frame. Default `style` is `underline` (also allowed: `text` for accent-colored words, `strike` for myth-busting). Every highlight renders in your single accent color, which lives as one renderer setting, not in the config. The highlight `text` must be an exact substring of its own block's text, 1-4 words.
- `background.type` is `photo` on every frame with a `src` filename named for what's in the photo. A solid color exists only as the missing-photo fallback, never authored.
- `screenshot` is `null` or a filename, paired with `screenshot_pos` in {upper, center, lower}.
- `text_position` in {top, center, bottom}, default `top`.
- `continues: true` (never on frame 1) inherits the previous frame's photo and anchor; omit `background` and `text_position` on continuation frames.
- `sticker` is `null`, or `{"type": "poll", "question": "...", "options": ["A", "B"]}`, or `{"type": "link", "url": "...", "label": "..."}`. Stickers are instructions for the posting checklist, never rendered into pixels (Instagram native stickers can't be baked into an image).

### The renderer spec

`render.py`, plain Python with Pillow as the only dependency. Deterministic: same config in, same pixels out. What it must do:

1. **Canvas 1080x1920.** One PNG per frame: `frame_<n>.png`.
2. **Photo background, cover-fit.** Scale and crop the photo to fill the canvas (honor `zoom` and `focus`, never letterbox). Bake EXIF orientation on load so phone photos sit upright. Note: Pillow can't read HEIC, so convert iPhone photos to JPG first.
3. **Grade the photo to pop.** A touch darker, more contrast, more saturation, slight sharpen. Keep it subtle, tune the exact values against test renders, and make them config-overridable per frame.
4. **A dark gradient only where the text sits.** Shape a vertical gradient so the area behind the text anchor darkens enough for white text to read, while the rest of the photo stays bright. This is the single biggest native-look factor: full-frame darkening looks like an ad.
5. **Text stack.** A bold sans-serif of your choice, white, anchored by `text_position` (default top). Make the headline clearly bigger than the support lines and tune the sizes against test renders. Wrap lines, keep a comfortable margin, small gap between blocks.
6. **The marker underline.** For a highlight span, draw a continuous rounded line in your accent color just under that phrase. The text above it stays white. For `text` style render the words in the accent color; for `strike` draw the line through them. The accent color is a single renderer-level setting.
7. **Continuation frames.** For `continues: true`: reuse the previous frame's graded photo, redraw the previous frame's entire text stack at pixel-identical positions but dimmed (a mid gray, highlights dropped), then draw this frame's blocks bright below it with a consistent gap. Chains accumulate: frame N carries everything N-1 showed.
8. **Screenshot card.** Composite the proof screenshot as a rounded-corner card with a soft shadow at `screenshot_pos`. Cap upscaling so a small crop stays sharp instead of blown up soft. Keep the text clear of the card.
9. **Graceful degrade.** A frame whose photo is missing renders on a near-black solid and logs a warning instead of crashing. A missing screenshot is skipped. The sequence always renders; you drop the asset and re-render.
10. **Emit `post-order.md`.** A checklist listing every frame in posting order, which frames carry a sticker instruction (poll or link, to be added by hand in the IG app), the suggested Highlight title, and a reminder to check the CTA keyword doesn't collide with any other running keyword.
11. **CLI.** `python3 render.py sequences/<slug>` renders all frames. `--frame N` re-renders one frame (plus any continuation frames that inherit from it). `--validate` checks the config without rendering.

### The asset library

The libraries are what let generation pick real photos instead of inventing filenames:

- `assets/backgrounds/` holds 15-30 photos of you and your world: at the desk, on calls, training, whiteboarding, lifestyle. Name files for their content (`desk-late-night.jpg`, `whiteboard-planning.jpg`, `gym-morning.jpg`).
- `assets/testimonials/` holds proof screenshots, cropped to just the message bubble, names and faces blurred. Keep the untouched originals elsewhere.
- Each folder has an `INDEX.md`: one line per file describing what's in it and what kind of beat it suits. Claude reads the INDEX at generation time and picks real files. When new photos land, ask Claude to look at them and append INDEX lines.

At render time, resolve a photo from the sequence's own `sources/` folder first, then fall back to the shared library and copy the file into `sources/`. That copy-on-use makes every rendered sequence self-contained.

### The build prompt

Paste this into Claude Code inside your project folder:

```
Read the story-sequences skill file. Build the system exactly to its Part 2 spec:

1. Create the folder layout.
2. Write render.py with Pillow as the only dependency, implementing all 11 points of
   the renderer spec, including --validate, --frame N, and post-order.md.
3. Download a bold sans-serif font family into assets/fonts/ (pick one you like from
   Google Fonts) and wire it in, and ask me for my accent color.
4. Create a sample sequence at sequences/sample-authority/ with a hand-written
   config.json (6 frames, three photo pairs, one underline highlight, one screenshot
   card) so we can test without generating anything.
5. Use any two photos I've put in assets/backgrounds/ for the sample (ask me to add
   photos if the folder is empty).
6. Render the sample and show me the frames.

Acceptance checks before you call it done: every frame is 1080x1920; text sits high
with the photo visible below; the underline is one clean accent-colored line under
the phrase; continuation frames show the previous text dimmed in its exact position
with the new line bright below; the screenshot renders as a rounded shadowed card;
a config that breaks a validation rule is refused with a clear error.
```

Iterate on the sample renders until the look is right (grade, gradient, sizes, gap). You're tuning taste once; every future sequence inherits it.

---

## Part 3 - Making sequences

### The generation prompt

Save this as `prompts/generate.md`. This is what you (or a one-line wrapper) run per idea. Fill the three placeholders at the top:

```
Topic: <one or two sentences, spoken or typed. What the sequence is about>
Type: <authority | authority_cta>
Proof notes: <optional: real numbers, client wins, screenshots you can supply>

You are writing an Instagram story sequence for me. Read the story-sequences skill
file first: follow its structure for my chosen type, its hook patterns, its design
rules, and (for authority_cta) its CTA formula exactly.

Voice: match the writing samples in this project. Short spoken sentences, specific
numbers, sentence case, no hashtags, no emojis, no em dashes, no hype words.

Then:
1. Read assets/backgrounds/INDEX.md and assets/testimonials/INDEX.md. Pick REAL
   files, matched to each beat. Only name a photo that doesn't exist if nothing in
   the library fits, and flag it clearly at the end.
2. Write sequences/<slug>/config.json to the schema. Structure it as photo pairs:
   each background gets a setup beat plus a continues payoff beat. 5-7 frames.
   At most one underline per frame, on the one phrase that matters. Often none.
3. For authority_cta: end on the CTA formula with a unique UPPERCASE keyword in its
   own block, underlined, and a link sticker hint if I have a resource page.
4. Run python3 render.py sequences/<slug> --validate and fix any errors.
5. Render it, then list any assets I still need to drop in.
```

### A worked example

Here's the shape of a finished config for an authority + CTA sequence, so you can see the level of specificity. The example user is an online fitness coach; adapt the domain to yours.

```json
{
  "slug": "check-in-template",
  "type": "authority_cta",
  "keyword": "PLAN",
  "highlight_title": "Coaching",
  "profile": { "handle": "@yourhandle" },
  "frames": [
    { "n": 1, "role": "hook",
      "blocks": [
        { "text": "Every client who starts with me does the same thing first." },
        { "text": "They send me their last three weeks of training.", "size": "med" } ],
      "background": { "type": "photo", "src": "gym-morning-coaching.jpg", "zoom": 1.0, "focus": "center" },
      "screenshot": null, "text_position": "top", "sticker": null },

    { "n": 2, "role": "hook", "continues": true,
      "blocks": [
        { "text": "And in 10 minutes I can tell them exactly why progress stopped.",
          "highlights": [ { "text": "exactly why", "style": "underline" } ] } ],
      "screenshot": null, "sticker": null },

    { "n": 3, "role": "authority",
      "blocks": [
        { "text": "It's almost never the workout." },
        { "text": "It's the week nobody planned for: travel, deadlines, kids sick.", "size": "med" } ],
      "background": { "type": "photo", "src": "desk-programming-plans.jpg", "zoom": 1.0, "focus": "center" },
      "screenshot": null, "text_position": "top", "sticker": null },

    { "n": 4, "role": "authority", "continues": true,
      "blocks": [
        { "text": "So every plan I write has a bad-week version built in.",
          "highlights": [ { "text": "bad-week version", "style": "underline" } ] } ],
      "screenshot": null, "sticker": null },

    { "n": 5, "role": "credibility",
      "blocks": [
        { "text": "Sarah's week 8 check-in came in this morning." },
        { "text": "Down 6kg. Two work trips in between.", "size": "med" } ],
      "background": { "type": "photo", "src": "coffee-checkin-reading.jpg", "zoom": 1.0, "focus": "center" },
      "screenshot": "client-message-week8.png", "screenshot_pos": "lower",
      "text_position": "top", "sticker": null },

    { "n": 6, "role": "bridge",
      "blocks": [
        { "text": "If your plan collapses every time work gets busy," },
        { "text": "the plan is the problem. Not you.", "size": "med",
          "highlights": [ { "text": "the plan is the problem", "style": "underline" } ] } ],
      "background": { "type": "photo", "src": "evening-walk-city.jpg", "zoom": 1.0, "focus": "center" },
      "screenshot": null, "text_position": "top", "sticker": null },

    { "n": 7, "role": "cta", "continues": true,
      "blocks": [
        { "text": "Reply with PLAN and I'll send you the exact check-in template my clients use.",
          "highlights": [ { "text": "PLAN", "style": "underline" } ] } ],
      "screenshot": null,
      "sticker": { "type": "link", "url": "https://your-site.com/your-resource", "label": "Get the template" } }
  ]
}
```

Notice: three photo pairs plus one solo proof frame. Four highlights across seven frames, never two on one frame. The keyword lives in its own sentence so the underline binds cleanly.

### Reviewing and tweaking

Generation gets you 90% there. Budget 5 minutes to review before posting: swap a photo that doesn't match the beat, tighten a line, move an underline to a stronger phrase. Edit `config.json` directly (or tell Claude what to change) and re-render just the touched frame with `--frame N`. The renderer is deterministic, so a one-word edit is a two-second round trip.

---

## Part 4 - Posting

### Hand-posting (start here)

Open `post-order.md`, post `frame_1.png` through `frame_N.png` back to back as one sequence, and add the native stickers the checklist calls out (a poll on the engagement frame, a link sticker on the CTA frame). Then save the sequence as a Highlight using the suggested title, so new profile visitors get the same authority journey on demand.

This takes 3 minutes and native stickers are worth having, so don't rush past this path.

### Auto-publish via a scheduler

Once the sequence quality is stable, schedule instead of hand-posting. I use Metricool: its API and scheduler support Instagram and Facebook stories, so Claude Code can push a whole sequence as one scheduled story post with all frames publishing back to back at a set time, no phone involved.

Link to Metricool: https://i.mtr.cool/omnifusion (this is an affiliate link and supports the channel)

Three things to know if you have Claude build the scheduling step:

- **Schedule the frames as ONE story post carrying all images in order**, not N separate posts. Separate posts can publish out of order; one post keeps the sequence intact.
- **Auto-published cards are bare.** No native stickers, no music. That's why the design puts the CTA keyword in the pixels: the ask survives automation. Sequences that need a poll or a tappable link sticker go out by hand.
- **Keep a small `schedule.json` record per sequence** and have the scheduling script refuse to double-post a sequence it already pushed. Cheap insurance.

### Wiring the keyword replies

The CTA only pays off if the reply gets answered fast:

- **Small scale:** answer story replies yourself. A keyword reply is the warmest inbound you'll get; send the resource and ask one follow-up question.
- **At volume:** use a DM automation tool (ManyChat is the standard) with a story-reply trigger per keyword: someone replies PLAN, the automation sends the resource link and hands the conversation to you (or your AI setter) for the follow-up.
- Either way, keep every running keyword unique across stories and reels, and retire keywords when a campaign ends.

---

## Going further

Once the core loop works, two upgrades are worth asking Claude Code for. Both are additions around the same config + renderer, so nothing gets rebuilt:

- **A local editor.** A small web app (FastAPI plus one static page) that lists sequences, previews frames, and lets you click a frame to edit text, move an underline, swap the photo from your library, or nudge brightness, re-rendering just that frame live. Turns the 5-minute review into a 2-minute one.
- **A real proof chart.** A script that renders a clean stats card from your own numbers (posts shipped, views over time, client results) as a PNG you drop into `results/`. Real data, honestly labeled, beats any screenshot hunt.

---

## Running the whole thing

1. Build the system with the build prompt, tune the sample renders until the look is right. One session, Claude Code does the coding.
2. Fill the two libraries: 15-30 named photos, a handful of cropped proof screenshots, INDEX lines for both. ~30 minutes, once.
3. Per sequence: speak or type the idea, run the generation prompt, review for 5 minutes, render, post or schedule. ~10 minutes end to end.
4. Cadence: at least twice a week, roughly 2 authority for every 1 CTA sequence.

## The one rule that makes it work

Authority first, ask second. The CTA sequence only converts because the authority sequences before it did the warming, and both only work because they show up every week. The system's job isn't to make one great sequence. It's to make showing up cost you 10 minutes.
