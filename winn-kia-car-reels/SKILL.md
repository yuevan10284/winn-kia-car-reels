---
name: winn-kia-car-reels
description: Turn a vehicle on the Winn Kia of Fremont lot into three branded 10-second vertical reels (1080x1920) — "heartfelt" (warm family story), "sky-drop" (the car falls from the sky and lands), and "exploded" (the car bursts into floating parts and reassembles). Pulls the real listing photos from winnkiaoffremont.com, generates each clip with Higgsfield Seedance 2.5 using those photos as references, then adds the Winn logos, a hook, captions written for that car, a music bed and an end card with the dealership address. Use this whenever the user names a Kia model, stock number, VIN or Winn Kia listing URL and wants a reel, video, social content, "the three videos", or "do the same for this car" — and for follow-ups such as changing captions, re-running one style, or redoing a clip.
---

# Winn Kia Car Reels

One car in, three finished reels out. Each reel is a 10 s, 9:16 Higgsfield clip of the exact car
from the listing photos, finished with:

- the Winn Auto Group logo at the top, the Winn Kia of Fremont logo on the end card
- a big hook line on screen from the very first frame
- two more captions and an end-card headline, all written for that specific car
- a music bed for the style, mixed under the clip's own sound effects
- the dealership address

| Style | What happens | Tone |
|---|---|---|
| `heartfelt` | A child sprints through the grass to the car, parent catches up, cabin, coastal drive-off | Warm, family |
| `sky-drop` | The car is already falling in frame one, slams onto a salt flat in a dust shockwave, drives off | Punchy, fun |
| `exploded` | Studio shot: the car snaps apart into floating parts, hangs, clicks back together | Premium, precise |

Default is all three. If the user names one style, make only that one.

Everything lives in this skill folder: `scripts/` (fetch, prompt, branding), `styles/*.json`
(video prompt, default captions, timings), `music/` (one bed per style), `brand.json` (logos,
dealer name, address).

## Before you start

Needs macOS with `ffmpeg`, `python3` with Pillow (`pip3 install pillow`), and the Higgsfield CLI
(`npm i -g @higgsfield/cli`, then `higgsfield auth login`). If any is missing, say which and stop.

- A workspace must be selected (`higgsfield workspace list`; if none, `higgsfield workspace set <id>`).
- Check the balance with `higgsfield workspace list`, tell the user the total for this run in one
  line, and go ahead unless the balance is too low. Don't ask again per clip. Re-rolls cost the same
  as a first take, so say so before redoing one.

### Cost (Seedance 2.5, 10 s, 9:16, with reference photos; checked October 2026)

| Setting | Credits per clip | Full set of 3 |
|---|---|---|
| 1080p (default) | 120 | 360 |
| 720p | 70 | 210 |
| `--draft true` (comes out 480p) | 30 | 90 |

Photo fetching, captions, logos, music and branding are free. Prices change, so confirm with
`higgsfield generate cost seedance_2_5 <same flags>` (free) before quoting a number. Use the 1080p
default unless the user asks for cheaper; 720p is the sensible saving for phone-only posting.

Drafts are for testing a changed prompt or a new style cheaply. A draft is a separate take: the
1080p version will not be the same footage, so don't promise the user "this exact clip, sharper".

## Steps

### 1. Find the car and pull its photos

```bash
S=~/.claude/skills/winn-kia-car-reels
python3 $S/scripts/fetch_listing.py --list telluride          # listing URLs for a model (add --condition used)
python3 $S/scripts/fetch_listing.py "<listing-url>" --out ~/Desktop/winn-kia-reels/<stock>
```

This writes `photos/01.jpg…`, `listing.json` (vehicle, colour, trim, VIN, stock) and
`contact-sheet.jpg`. If the user gave only a model, pick a listing that has real lot photos and say
which stock number you used. Work in `~/Desktop/winn-kia-reels/<stock>/` unless the user names a folder.

If the fetch finds no photos, the site layout may have changed: open the listing in the browser,
collect the gallery image URLs there, and download them into `photos/` by hand.

### 2. Look at the photos

Read `contact-sheet.jpg`. Two things come out of this:

- **Reference set** — pick about six photos: front three-quarter, side, rear three-quarter, straight
  rear, straight front, and one interior. Skip close-ups of switches, window stickers and anything
  with a watermark banner across the car.
- **The look** — one clause describing what makes this exact car recognisable: paint colour, grille,
  wheels, roof rails, lights, trim details. Describe only what the photos show. This goes into every
  prompt and is the main thing keeping the generated car faithful.

### 3. Write the captions for this car

Every car gets its own wording; identical captions on every post make the feed look automated.
For each style, write `<style>-copy.json` in the car's folder:

```json
{
  "captions": [
    ["DON'T BLINK."],
    ["The new Telluride", "just landed."],
    ["And it's parked", "in Newark."]
  ],
  "headline": ["On the lot now.", "Come take a look."]
}
```

Three captions (the first is the hook) and a two-line end-card headline. Lines must be short: about
22 characters each, two lines at most per caption. The style's own captions in `styles/*.json` show
the intended rhythm and are the fallback if no copy file is passed.

**The hook is the line that matters.** It is on screen from frame zero, in large type, while the
most dramatic moment of the clip plays. Make it earn the next second:

- Six words or fewer. A question, a dare or an unfinished thought: "Who's riding with you?",
  "DON'T BLINK.", "WHAT'S INSIDE A TELLURIDE?"
- It should make sense with the first second of that style's footage (a child running, a car
  falling, a car bursting apart).
- Not the model name alone, not "Introducing…", not "Check this out".

For the rest, write the way someone at the dealership would talk about this particular car. Think
about who buys it — a three-row SUV, a commuter EV and a first car each get different lines — and
name the life it fits rather than its features. Keep it warm and specific to Newark, Fremont and the
Bay Area where that comes naturally. Follow the on-screen rules at the end of this file: no prices,
no specs, no claims you have not verified.

### 4. Generate the clips

Build each prompt from its style file, then generate. Run the styles in parallel as background
commands; each takes a few minutes.

```bash
P=$(python3 $S/scripts/prompt.py sky-drop --vehicle "white 2027 Kia Telluride X-Line" \
      --look "glacial white pearl paint, black grille, black wheels, black roof rails, vertical LED lights")
higgsfield generate create seedance_2_5 --prompt "$P" --mode omni_reference \
  --image photos/01.jpg --image photos/02.jpg --image photos/03.jpg \
  --image photos/04.jpg --image photos/08.jpg --image photos/09.jpg \
  --duration 10 --resolution 1080p --aspect_ratio 9:16 --wait --wait-timeout 20m
```

The command prints the result URL. Download it as `<style>-raw.mp4`.

Why the prompts are written the way they are, so edits keep what works:

- **Action in frame one.** Each prompt opens mid-action with no establishing shot, because viewers
  decide in the first second.
- **No on-screen text.** The branding step adds all text; text the video model draws comes out garbled.
- **Sound effects only, no music.** The music bed is added afterwards, and two music tracks clash.
- **Car in the upper two thirds.** The captions and end card sit in the lower third.
- **10 seconds.** The caption timings in each style file assume it.

### 5. Check each raw clip

Pull a strip of frames, including the first half second, and look at it before branding:

```bash
ffmpeg -loglevel error -y -i sky-drop-raw.mp4 \
  -vf "select='eq(n,2)+eq(n,30)+eq(n,60)+eq(n,110)+eq(n,160)+eq(n,200)+eq(n,235)',scale=270:480,tile=7x1" \
  -frames:v 1 -fps_mode vfr sky-drop-frames.jpg
```

Check that the first frame already has the action in it, that the car matches the photos (colour,
wheels, grille, badge) and stays in frame, and that nothing is broken (melted wheels, wrong badge,
gibberish text, extra doors). `exploded` is the most likely to come out wrong. If a clip fails, tell
the user what is wrong and what a re-roll costs rather than quietly spending more credits.

If the key moment lands at a different time than the captions expect (for example the car touches
down at 2.5 s instead of 1.5 s), copy the style JSON into the car's folder, shift that caption's
`start` / `end`, and pass the copy to `--style`.

### 6. Add logos, captions and music

```bash
python3 $S/scripts/brand_video.py --input sky-drop-raw.mp4 --style $S/styles/sky-drop.json \
  --vehicle "2027 Kia Telluride" --copy sky-drop-copy.json --out sky-drop-final.mp4
```

- `--vehicle` is the short public name (year, make, model) for the end card.
- `--copy` is the per-car wording from step 3.
- Music defaults to `music/<style>.m4a`, mixed under the clip's sound effects. Pass `--music <file>`
  to use another track or `--music none` to keep only the clip's own audio.
- Logos are downloaded from the dealership's sites on first use and cached in `assets/`. If a
  download fails the script falls back to a text wordmark and says so; mention that to the user.
- Output is always 1080x1920, whatever resolution the clip was generated at.

Look at a few frames of the final file to confirm the text is readable against the footage, then
open the finished videos for the user.

### 7. Report

Give the paths to the final files, the stock number and listing used, credits spent, the captions
you wrote, and anything that looked off. Note that the people and scenery are AI-generated and the
clips have been checked as still frames, not watched with sound, unless you did more.

## Rules for what goes on screen

These protect the dealership, so hold to them even when asked to move fast:

- **No prices, payments, APRs, rebates or "deal" wording by default.** Advertised prices carry
  disclosure requirements. If the user wants a price on screen, take it from the live listing the
  same day, include the stock number or VIN, and tell the user it needs the dealership's own
  disclosure text before posting.
- **No spec or feature claims** (range, MPG, towing, seating, warranty) unless the user supplies
  the figure or you read it from the live listing or kia.com in this session.
- **"On the lot" / "just landed" lines** are only true while the car is in inventory. The listing
  was live when you fetched it; say so, and mention it will go stale once the car sells.
- **The exploded view is an illustration.** The generated parts are not accurate engineering, so
  never label parts or use the clip to explain how the car works.
- The address and dealer name come from `brand.json`; don't retype them.

## Changing the defaults

- **Music:** replace `music/<style>.m4a` with any 10 s or longer track. The current beds were
  generated with `higgsfield generate create sonilo_music --prompt "…" --duration 12 --wait`
  (under 1 credit each).
- **Logos:** edit the `logos` block in `brand.json` (source URL, width, and `white: true` to recolour
  a dark logo for video), or drop a PNG with the matching `file` name into `assets/`.
- **A new style:** copy a `styles/*.json`, rewrite `prompt`, `captions` and `end_card`, add a music
  bed with the same name, and test it with `--draft true` before spending on 1080p.

## Notes

- macOS only as written: text uses Avenir Next from `/System/Library/Fonts`, and the local ffmpeg
  has no `drawtext`, which is why captions are rendered with Pillow and overlaid.
- Text stays out of the top ~220 px and bottom ~330 px so Reels and TikTok UI doesn't cover it.
