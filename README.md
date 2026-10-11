# Winn Kia Car Reels

A Claude skill that turns a vehicle on the Winn Kia of Fremont lot into three branded
10-second vertical reels (1080x1920), ready for Instagram Reels or TikTok.

| Style | What happens | Tone |
|---|---|---|
| `heartfelt` | Golden-hour overlook, a parent and child walk to the car, cabin, coastal drive-off | Warm, family |
| `sky-drop` | The car falls from the sky onto a salt flat, lands in a dust shockwave, drives off | Punchy, fun |
| `exploded` | Studio shot: the car separates into floating parts, then snaps back together | Premium, precise |

For each car, the skill:

1. Pulls the real listing photos and details (model, colour, VIN, stock number) from winnkiaoffremont.com.
2. Generates each clip with Higgsfield (Seedance 2.5), using the photos as references so the car matches.
3. Burns in the "WINN KIA / OF FREMONT" wordmark, three captions, and an end card with the dealership address.

## Requirements

- macOS (captions use the system Avenir Next font)
- [Claude Code](https://claude.com/claude-code)
- `ffmpeg` — `brew install ffmpeg`
- `python3` with Pillow — `pip3 install pillow`
- A Higgsfield account with credits, and its CLI

## Setup

**1. Install the Higgsfield CLI and sign in**

```bash
npm i -g @higgsfield/cli
higgsfield auth login
```

The login opens a browser tab; sign in there. Then pick the workspace that gets billed:

```bash
higgsfield workspace list
higgsfield workspace set <workspace_id>
```

**2. Install the skill**

```bash
git clone https://github.com/yuevan10284/winn-kia-car-reels.git
mkdir -p ~/.claude/skills
cp -R winn-kia-car-reels/winn-kia-car-reels ~/.claude/skills/
```

**3. Restart Claude Code** so it picks up the new skill.

## Using it

Open Claude Code and ask in plain language. Any of these work:

```
make the three reels for the 2027 Telluride
make a sky-drop reel for stock J7186
do the reels for https://www.winnkiaoffremont.com/viewdetails/new/<vin>/<listing>
```

Claude tells you the credit cost up front, generates the clips (a few minutes each), checks them,
and saves everything to `~/Desktop/winn-kia-reels/<stock>/`:

```
photos/                 the listing photos
contact-sheet.jpg       all photos in one image
listing.json            vehicle details
heartfelt-raw.mp4       clip without text
heartfelt-final.mp4     finished reel
sky-drop-final.mp4
exploded-final.mp4
```

Follow-ups work too: "change the last caption to …", "redo the exploded one", "just the heartfelt
style for this car".

## Cost

Each person spends their own Higgsfield credits. Quotes from October 2026, per 10-second clip:

| Setting | Credits per clip | Full set of 3 |
|---|---|---|
| 1080p (default) | 120 | 360 |
| 720p | 70 | 210 |
| 480p or draft | 30 | 90 |

On the Plus plan ($49/month for 1,000 credits) that is roughly $5 to $6 per 1080p video, or about
$15 to $18 per car. A redo costs the same as a first take. Photo fetching, captions and branding
are free. Ask Claude for "720p" to cut the cost by about 40%.

## Customizing

Everything editable lives in the skill folder (`~/.claude/skills/winn-kia-car-reels/`):

| File | What it controls |
|---|---|
| `brand.json` | Wordmark, dealership name and address on the end card |
| `styles/heartfelt.json`, `styles/sky-drop.json`, `styles/exploded.json` | The video prompt, the captions, and when each caption appears |
| `scripts/fetch_listing.py` | Which website the photos come from |

To add a fourth style, copy one of the `styles/*.json` files, rewrite its `prompt`, `captions`
and `end_card`, and ask Claude for that style by name.

To use it for a different dealership, change `brand.json` and the `SITE` address at the top of
`scripts/fetch_listing.py`. The photo fetcher expects the same website platform Winn Kia uses, so
other sites may need the photos downloaded by hand.

## Running the scripts yourself

Claude normally runs these for you, but they work on their own:

```bash
S=~/.claude/skills/winn-kia-car-reels

# list a model's listings, then pull one car's photos
python3 $S/scripts/fetch_listing.py --list telluride
python3 $S/scripts/fetch_listing.py "<listing-url>" --out ~/Desktop/winn-kia-reels/J7186

# print a style's video prompt for a car
python3 $S/scripts/prompt.py sky-drop --vehicle "white 2027 Kia Telluride X-Line" \
  --look "glacial white pearl paint, black grille, black wheels, black roof rails"

# add branding and captions to a generated clip
python3 $S/scripts/brand_video.py --input sky-drop-raw.mp4 --style $S/styles/sky-drop.json \
  --vehicle "2027 Kia Telluride" --out sky-drop-final.mp4
```

## What it won't put on screen

- **No prices, payments, rebates or "deal" wording** by default. Advertised prices need the
  dealership's own disclosure text.
- **No spec or feature claims** (range, MPG, towing, warranty) unless you supply the figure.
- **"Now on the lot"** on the sky-drop end card is only true while that car is in inventory.
- The people and scenery are AI-generated, and the exploded view is an illustration, not accurate
  engineering.

Review every video before posting. See `winn-kia-car-reels/SKILL.md` for the full rules Claude follows.

## Troubleshooting

- **"No workspace selected"** — run `higgsfield workspace list`, then `higgsfield workspace set <id>`.
- **"Session expired" / "Not authenticated"** — run `higgsfield auth login` again.
- **No photos found** — the listing may have sold or the site changed; try another listing URL.
- **`No module named PIL`** — run `pip3 install pillow`.
- **The car looks wrong in a clip** — ask Claude to redo that style; it costs the same as the first take.

---

Not affiliated with or endorsed by Kia or Higgsfield.
