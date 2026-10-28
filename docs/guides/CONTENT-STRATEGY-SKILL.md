---
name: content-strategy
description: Turn two documents (an ICP doc and an offer doc) into a 20-idea content slate written in your own voice. Ten ideas built for reach, ten built to convert. Use when planning content, batching scripts, or you feel like your posts aren't landing with buyers.
---

# The 2-Document Content Strategy

The reason most content flops isn't the hook. It's that you never told the AI who you're talking to.

This skill fixes that. You build two documents once, an ICP doc (who you're actually talking to) and an offer doc (what you sell and why it's worth it). Then a scriptwriter, taught to write the way you talk, turns those two documents into a content slate aimed at the exact person you want to book.

The whole system in one line:

> ICP doc (who) + offer doc (what) -> scriptwriter (your voice) -> 20 content ideas, 10 for reach and 10 to convert.

Build the two docs once. Generate content off them forever.

---

## How to use this

Two ways, pick one:

1. **As a Claude Code skill (recommended).** Save this file as `.claude/skills/content-strategy/SKILL.md` inside your project. Then just tell Claude Code: "use the content-strategy skill" and it walks you through all three steps.
2. **As a paste-in.** Drop this whole file into Claude Code (or the Claude app) and say "run this with me." It will do the same thing, one step at a time.

You do Step 1 and Step 2 once. After that, Step 3 is the part you run every time you want a fresh batch of ideas. Be honest with yourself on the setup: the first pass takes 20 to 30 minutes, mostly getting a call transcript together. You only do it once. Every batch of 20 ideas after that is Step 3 on its own, about five minutes, any time you want content.

A note on the offer doc: it's built around the value equation from Alex Hormozi's *$100M Offers*. If you own the book, upload it and let Claude Code use the whole thing. If you don't, the framework is distilled into Step 2 so it still works.

---

## Step 1 - Build your ICP doc

Don't guess who you're talking to. Almost everyone guesses, writes a vague "my ideal client is a coach who wants more clients," and then wonders why the content doesn't convert. The fix is to reverse-engineer a real one.

If you've had a sales call with a dream client, you already have everything you need. The transcript holds their real situation, their actual pains, and the outcome they're really after, in their own words. That last part matters most: the language they use is the language your hooks should use.

### If you have a sales-call transcript (best path)

Record one call (Fathom, Otter, Zoom, anything), export the transcript, and run this:

```
You're helping me build an ICP document from a real sales call.

Here is the transcript of a call with a dream client:

<paste transcript>

Reverse-engineer this person into an ICP doc. Don't summarize the call, profile the buyer behind it. Pull out:

1. SITUATION - where they are right now, concretely. Role, business, stage, what their day actually looks like.
2. PAINS - the specific problems they're feeling, ranked by how much they ache. Use their own words wherever you can.
3. DESIRED OUTCOME - what they actually want, the real outcome, not the surface request. What does "this worked" look like to them?
4. OBJECTIONS AND FEARS - what's holding them back, what they're skeptical of, what they've tried that failed.
5. THEIR LANGUAGE - the exact phrases, words, and metaphors they use to describe their problem and their goal. Quote them.

Be specific and concrete. If something isn't in the transcript, say "not stated" rather than inventing it.
```

### If you don't have a transcript yet

Use this instead. It's a guided interview. Answer it out loud or in writing, and Claude Code turns your answers into the same doc.

```
I want to build an ICP document but I don't have a sales-call transcript yet. Interview me.

Ask me one question at a time about my single best-fit client (a real person if possible: name them in your head). Cover their situation, their top three pains, the outcome they actually want, their objections, and the exact words they use. Push me to be specific when I'm being vague. After about 8 to 10 questions, write the finished ICP doc using the template below.
```

### The ICP doc template

This is the shape of the finished doc. Save it as `icp.md`.

```
# ICP - [who, in one line]

## Situation
- Role / business:
- Stage:
- What their day looks like:

## Pains (ranked)
1.
2.
3.

## Desired outcome
- The real outcome (not the surface request):
- What "this worked" looks like to them:

## Objections and fears
-
-

## Their language (verbatim)
- "..."
- "..."
```

One ICP per doc. If you serve two very different buyers, build two docs and generate separately. Mixing them is how you end up talking to nobody.

---

## Step 2 - Build your offer doc

Your content's job is to make people want the offer. So the offer has to be sharp before the content can sell it. This step pressure-tests what you sell against the value equation and rewrites it stronger.

The value equation (from *$100M Offers*) is a ratio:

> value = (dream outcome x perceived likelihood of achievement) / (time delay x effort and sacrifice)

So perceived value goes up when you raise the **dream outcome** and the **perceived likelihood** they'll hit it, and down as **time delay** and **effort and sacrifice** climb. A strong offer maxes the top two and shrinks the bottom two. The lever most people leave on the table is perceived likelihood: a buyer who has failed before doesn't need a bigger promise, they need to believe it'll work for them this time.

### The prompt

If you own *$100M Offers*, upload the PDF first, then run this. If you don't, the equation above is enough for Claude Code to work with.

```
You're helping me sharpen my offer using the value equation from $100M Offers:
value = (dream outcome x perceived likelihood of achievement) / (time delay x effort and sacrifice).

Here's my ICP doc, use it as the evidence for everything below:
<paste icp.md>

Here's what I sell right now:
- Offer: <name it>
- What they get: <deliverables>
- Price: <price>
- The promise I make today: <your current pitch>

Do four things:

1. SCORE my current offer 1 to 10 on each of the four variables (dream outcome, perceived likelihood, time delay, effort and sacrifice). For each score, give a one-line reason that QUOTES the ICP doc. If the ICP doc has no evidence for a variable, say "not enough in the ICP doc, go back to Step 1" instead of guessing. Then name the single variable dragging value down most.
2. SHARPEN the dream outcome so it's specific and uses my ICP's own words for what they want.
3. RAISE perceived likelihood (usually the biggest lever): name the proof, guarantee, or risk reversal that makes them believe it'll work for THEM, given what they've already tried and failed.
4. SHRINK time delay and effort: where can I show a faster first win or take work off their plate?

Then name the one highest-leverage fix and rewrite one sentence of my offer to prove it. Finally, write the finished offer doc using the template below. Keep it concrete. No hype words.
```

### The offer doc template

Save it as `offer.md`.

```
# Offer - [name]

## Who it's for
[one line, points at the ICP doc]

## Dream outcome
[the specific result, in their language]

## The promise
[what they get, by when]

## Why they'll believe it (proof + risk reversal)
-
-

## How it works (the mechanism, plainly)
1.
2.
3.

## Price and what's included
-
```

---

## Step 3 - Generate the content slate

Now it clicks. You feed both documents into the scriptwriter and ask for 20 ideas: ten built for reach, ten built to convert. This is the step you re-run whenever you want fresh content.

### First, teach it your voice

Content that sounds like a press release doesn't get watched. Before you generate, give Claude Code a voice sample so the ideas come back sounding like you, not like AI.

```
Here's how I talk. Learn it and write everything in this voice from now on.

<paste 3 to 5 things you've actually written or said: captions, a transcript of you talking, a voice note typed out, DMs>

Voice rules:
- Short, complete sentences. One idea per sentence. Vary the length, a longer setup then two or three short hammers.
- Write the way I speak, not the way people write. Contractions always.
- Lead with the result or the bold claim. No warm-up.
- Plain language a beginner understands. Unpack any jargon immediately.
- Prove claims with one specific number or one before/after, never vague.
- No em dashes. No hype words (unlock, leverage, seamless, game-changer, supercharge). No "it's not just X, it's Y." No emoji. No hashtags.
- Confident, warm, direct, talking to one person. Give value, don't bait.
```

### Then generate

```
Read both documents:

ICP doc:
<paste icp.md>

Offer doc:
<paste offer.md>

Write me 20 content ideas in my voice, split into two halves.

TEN FOR REACH. Top of funnel, for people who don't know me yet. Each one leads with a broad, debatable claim or a named trending tool or method, something a stranger would stop for. Contrarian takes, surprising mechanisms, "most people get X wrong." The job is new eyeballs, not a sale. Still in my world, just wider than my exact buyer.

TEN TO CONVERT. Middle and bottom of funnel, for the exact person in the ICP doc. Each one leads with a named ICP pain or a piece of proof. Speak to one specific problem, show I can solve it, make the offer obvious without being salesy. The job is to pull DMs and qualify buyers.

For each of the 20 ideas give me:
- IDEA (one line, what it's about)
- HOOK (the first line, one scroll-stop: short enough to read before the thumb moves, about 6 to 12 words, two short sentences allowed. Use one of: problem-based "you're losing X because of Y", counter-intuitive "this X is actually hurting your Y", numbers-based "3 things killing your X", or pattern-interrupt "stop doing X until you see this")
- ANGLE (the one point the piece makes, in a sentence)
- FORMAT (talking head, demo, carousel, etc.)
- WHY IT LANDS (which ICP pain or offer strength it hits)

Number them 1 to 20, reach first, convert second. Make every hook use my ICP's own words, not generic phrasing. No two ideas may share the same core claim: if two overlap, replace one.
```

### What you get back

A ranked content slate, 20 ideas, each with a ready hook and a clear angle, every one aimed at the person in your ICP doc. Pick the ones you'll record, and you've got weeks of content planned in the time it used to take to write one caption.

---

## What it looks like filled in

Here's a real example so you can see the depth this needs. Don't copy it. Match how specific it gets, especially how it pulls the buyer's exact words.

**The user:** an online fitness coach selling an $8,000 6-month 1:1 program to busy male professionals.

**icp.md (condensed):**

```
# ICP - the successful operator who runs his business but not his body

## Situation
38 to 45, runs a demanding business, married with kids, 60-hour weeks, energy gone
by 3pm. Money isn't the problem, his body is.

## Pains (ranked)
1. Identity gap: "I look in the mirror and I don't recognize the guy."
2. Broken self-trust: goes hard for three weeks, then "a big deal blows up and it all
   falls apart."
3. Knowing-doing gap: "I know what to do. I just can't make it fit my life."

## Desired outcome
To be one man again, the operator who runs his company AND his body. "Take my shirt
off at the pool and not think about it." Keep up with his kids.

## Their language (verbatim)
- "I don't trust myself to stick with anything anymore."
- "The guy who runs my business also runs his own body. Right now those feel like
  two different people."
```

**offer.md (the sharpening that mattered):** his current promise, "lose fat with a plan that fits your schedule," scored lowest on perceived likelihood, a 3 out of 10, because he'd failed four programs and nothing made him believe this time was different. The fix: a built-in "busy-week protocol" (a 20-minute minimum dose for the week a deal blows up) plus a 30-day first-win guarantee, so the risk of another failed sprint sits on the coach, not the client.

**3 of the 20 ideas it produced:**

- REACH. Hook: "You don't quit because you're lazy." Angle: the three-week collapse is a design failure, the plan had no setting for a chaotic week. Why it lands: removes the shame around pain #2, broad enough for cold reach.
- CONVERT. Hook: "He'd quit 4 programs before he found me." Angle: a client with the same restart history got lean in six months on 35 minutes a day. Why it lands: raises perceived likelihood with proof from a man just like the buyer.
- CONVERT. Hook: "You're two men right now. Pick one." Angle: the operator and the out-of-shape guy can't both win for long, one call ends it. Why it lands: lands the buyer's deepest line ("two different people") on a clean book-a-call ask.

Notice every strong hook is the buyer's own language turned into a line. That's the whole game.

---

## Running the whole thing

1. Drop a sales-call transcript into Claude Code and build `icp.md` (Step 1). ~7 min.
2. Tell it what you sell, sharpen it, save `offer.md` (Step 2). ~7 min.
3. Paste a voice sample, then both docs, and ask for the 20 ideas (Step 3). ~5 min.

After the first pass, you keep `icp.md` and `offer.md`. Generating a new batch is just Step 3, about five minutes, any time you need content.

## The one rule that makes it work

You never told the AI who you're talking to. That's the whole reason generic content fails. Once the ICP doc and the offer doc are sitting in front of it, every idea it writes is aimed at a real person with a real problem you can actually solve. That's the difference between content that gets likes and content that books calls.
