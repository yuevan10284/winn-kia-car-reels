---
name: winn-kia-car-reels
description: Turn a vehicle on the Winn Kia of Fremont lot into three branded 10-second vertical reels (1080x1920) — "heartfelt" (warm family story), "sky-drop" (the car falls from the sky and lands), and "exploded" (the car separates into floating parts and reassembles). Pulls the real listing photos from winnkiaoffremont.com, generates each clip with Higgsfield Seedance 2.5 using those photos as references, then burns in Winn Kia branding, captions and an end card with the dealership address. Use this whenever the user names a Kia model, stock number, VIN or Winn Kia listing URL and wants a reel, video, social content, "the three videos", or "do the same for this car" — and for follow-ups such as changing captions, re-running one style, or redoing a clip.
---

# Winn Kia Car Reels

One car in, three finished reels out. Each reel is a 10 s, 9:16, 1080p Higgsfield clip of the
exact car from the listing photos, with a persistent "WINN KIA / OF FREMONT" wordmark, three
story captions and an end card inviting people to the dealership.

| Style | What happens | Tone |
|---|---|---|
| `heartfelt` | Golden-hour overlook, parent and child walk to the car, cabin, coastal drive-off | Warm, family |
| `sky-drop` | Empty salt flat, the car falls from the sky and lands in a dust shockwave, orbit, drives off | Punchy, fun |
| `exploded` | Studio shot, the car separates into floating parts, hangs, snaps back together | Premium, precise |

Default is all three. If the user names one style, make only that one.

Everything lives in this skill folder: `scripts/` (fetch, prompt, branding), `styles/*.json`
(prompt + captions + timings per style), `brand.json` (wordmark, dealer name, address).

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
| 480p or `--draft true` | 30 | 90 |

Photo fetching, captions and branding are free. Prices change, so confirm with
`higgsfield generate cost seedance_2_5 <same flags>` (free) before quoting a number. Use the 1080p
default unless the user asks for cheaper; 720p is the sensible saving for phone-only posting.

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

### 3. Generate the clips

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

The prompts ask for no on-screen text because the branding step adds all text; text the video model
draws itself comes out garbled. Keep the 10 s length — the caption timings in each style file assume it.

### 4. Check each raw clip

Pull a strip of frames and look at it before branding:

```bash
ffmpeg -loglevel error -y -i heartfelt-raw.mp4 -vf "fps=0.8,scale=270:480,tile=8x1" -frames:v 1 heartfelt-frames.jpg
```

Check that the car matches the photos (colour, wheels, grille, badge), that it stays in frame, and
that nothing is broken (melted wheels, wrong badge, gibberish text, extra doors). `exploded` is the
most likely to come out wrong. If a clip fails, tell the user what is wrong and what a re-roll costs
rather than quietly spending more credits.

### 5. Add branding and captions

```bash
python3 $S/scripts/brand_video.py --input heartfelt-raw.mp4 --style $S/styles/heartfelt.json \
  --vehicle "2027 Kia Telluride" --out heartfelt-final.mp4
```

`--vehicle` is the short public name (year, make, model) used in the end card. Captions scale down
automatically if a long model name would overflow. Look at a few frames of the final file to confirm
the text is readable against the footage, then open the finished videos for the user.

To change wording or timing for one car, copy the style JSON into the car's folder, edit the
`captions` / `end_card` there, and pass that copy to `--style`. Edit the files in `styles/` only
when the user wants the change for every future car.

### 6. Report

Give the paths to the three final files, the stock number and listing used, credits spent, and
anything that looked off. Note that the people and scenery are AI-generated and the clips have been
checked as still frames, not watched with sound, unless you did more.

## Rules for what goes on screen

These protect the dealership, so hold to them even when asked to move fast:

- **No prices, payments, APRs, rebates or "deal" wording by default.** Advertised prices carry
  disclosure requirements. If the user wants a price on screen, take it from the live listing the
  same day, include the stock number or VIN, and tell the user it needs the dealership's own
  disclosure text before posting.
- **No spec or feature claims** (range, MPG, towing, seating, warranty) unless the user supplies
  the figure or you read it from the live listing or kia.com in this session.
- **"Now on the lot"** (the `sky-drop` end card) is only true while the car is in inventory.
  The listing was live when you fetched it; say so, and mention it will go stale once the car sells.
- **The exploded view is an illustration.** The generated parts are not accurate engineering, so
  never label parts or use the clip to explain how the car works.
- The wordmark is plain text. Use a real logo only if the user provides the file.
- The address and dealer name come from `brand.json`; don't retype them.

## Notes

- macOS only as written: text uses Avenir Next from `/System/Library/Fonts`, and the local ffmpeg
  has no `drawtext`, which is why captions are rendered with Pillow and overlaid.
- Text stays out of the top ~220 px and bottom ~330 px so Reels and TikTok UI doesn't cover it.
