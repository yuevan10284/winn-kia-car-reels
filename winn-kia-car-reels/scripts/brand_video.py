#!/usr/bin/env python3
"""Burn Winn branding, captions, an end card and a music bed onto a raw generated clip.

  brand_video.py --input raw.mp4 --style ../styles/heartfelt.json \
                 --vehicle "2027 Kia Telluride" --out final.mp4 [--copy copy.json]

Text is rendered with Pillow (the local ffmpeg has no drawtext filter) and
composited with ffmpeg overlay + alpha fades. Timings come from the style JSON;
logos, dealer name and address come from brand.json. --copy supplies per-car
wording: {"captions": [["line", ...], ...], "headline": ["line", ...]}.
"""
import argparse
import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONT = "/System/Library/Fonts/Avenir Next.ttc"
BOLD, DEMI, MEDIUM, HEAVY = 0, 2, 5, 8
MAX_TEXT_W = 960
WHITE = (255, 255, 255, 255)
SOFT = (255, 255, 255, 225)
SKILL = Path(__file__).resolve().parent.parent


def font(size, index):
    return ImageFont.truetype(FONT, size, index=index)


def fit(text, size, index, tracking=0):
    """Largest font <= size that keeps the line inside the safe width."""
    while size > 20:
        f = font(size, index)
        if f.getlength(text) + tracking * (len(text) - 1) <= MAX_TEXT_W:
            return f
        size -= 2
    return font(size, index)


def gradient(top_alpha, bottom_alpha, y0, y1):
    strip = Image.new("L", (1, y1 - y0))
    for y in range(y1 - y0):
        t = y / max(1, y1 - y0 - 1)
        strip.putpixel((0, y), int(top_alpha + (bottom_alpha - top_alpha) * t))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black = Image.new("RGBA", (W, y1 - y0), (0, 0, 0, 255))
    black.putalpha(strip.resize((W, y1 - y0)))
    img.paste(black, (0, y0))
    return img


def text_layer(lines):
    """lines: (text, font, y, fill, tracking). Centered with a soft drop shadow."""
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for text, f, y, fill, tracking in lines:
        widths = [f.getlength(c) + tracking for c in text]
        x = (W - (sum(widths) - tracking)) / 2
        for c, w in zip(text, widths):
            ImageDraw.Draw(shadow).text((x, y + 3), c, font=f, fill=(0, 0, 0, 210))
            ImageDraw.Draw(layer).text((x, y), c, font=f, fill=fill)
            x += w
    return Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)), layer)


def load_logo(spec):
    """Fetch (once) and prepare a logo: trimmed, optionally forced to white, scaled to spec width.

    Logos are downloaded from the dealership's own sites and cached in assets/ rather than
    shipped with the skill. Returns None if unavailable so callers can fall back to text.
    """
    if not spec:
        return None
    cache = SKILL / "assets" / spec["file"]
    try:
        if not cache.exists():
            cache.parent.mkdir(exist_ok=True)
            req = urllib.request.Request(spec["url"], headers={"User-Agent": "Mozilla/5.0"})
            cache.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        img = Image.open(cache).convert("RGBA")
    except Exception as e:  # network down, URL moved, bad file
        print(f"logo unavailable ({spec['file']}): {e} — using text instead")
        return None
    img = img.crop(img.getchannel("A").getbbox())
    if spec.get("white"):
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        white.putalpha(img.getchannel("A"))
        img = white
    w = spec["width"]
    return img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)


def paste_logo(canvas, logo, y):
    """Centered logo with a soft shadow so it holds up on bright footage."""
    x = (W - logo.width) // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black = Image.new("RGBA", logo.size, (0, 0, 0, 255))
    black.putalpha(logo.getchannel("A").point(lambda a: a * 190 // 255))
    shadow.paste(black, (x, y + 3))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))
    canvas.alpha_composite(logo, (x, y))


def render(style, brand, vehicle, copy, tmp):
    """Write overlay PNGs; return [(path, fade_in_at or None, fade_out_at or None)]."""
    layers = []
    fill = lambda t: t.format(vehicle=vehicle, VEHICLE=vehicle.upper())
    logos = brand.get("logos", {})

    # Persistent header, kept below the Reels/TikTok top UI zone.
    img = gradient(150, 0, 0, 520)
    header = load_logo(logos.get("header"))
    if header:
        paste_logo(img, header, 228)
    else:
        top, sub = brand["wordmark"]
        img = Image.alpha_composite(img, text_layer(
            [(top, font(58, BOLD), 232, WHITE, 14), (sub, font(26, DEMI), 312, SOFT, 12)]))
    img.save(tmp / "brand.png")
    layers.append((tmp / "brand.png", 0.2, None))

    # Captions, kept above the bottom UI zone. The first one is the hook: bigger, heavier,
    # and on screen from frame 0 with no fade-in, because the first second decides the view.
    base = gradient(0, 185, 1100, H)
    wording = copy.get("captions") or [c["lines"] for c in style["captions"]]
    for i, (cap, lines_in) in enumerate(zip(style["captions"], wording)):
        texts = [fill(t) for t in lines_in]
        hook = i == 0
        size, weight, step = (92, HEAVY, 108) if hook else (64, DEMI, 84)
        y0 = (1370 if hook else 1400) - (len(texts) - 1) * step // 2
        lines = [(t, fit(t, size, weight), y0 + j * step, WHITE, 0) for j, t in enumerate(texts)]
        p = tmp / f"cap{i}.png"
        Image.alpha_composite(base, text_layer(lines)).save(p)
        layers.append((p, None if hook else cap["start"], cap["end"]))

    # End card: kicker, headline, dealer logo (or name), address.
    end = style["end_card"]
    kicker = fill(end["kicker"])
    head = [fill(t) for t in (copy.get("headline") or end["headline"])]
    y = 1262 - (len(head) - 2) * 84
    lines = [(kicker, fit(kicker, 34, DEMI, 8), y - 62, SOFT, 8)]
    lines += [(t, fit(t, 68, DEMI), y + j * 84, WHITE, 0) for j, t in enumerate(head)]
    lines.append((brand["address"], fit(brand["address"], 36, MEDIUM), 1556, SOFT, 0))
    dealer = load_logo(logos.get("end_card"))
    if not dealer:
        lines.append((brand["name"], font(44, BOLD), 1480, WHITE, 0))
    img = Image.alpha_composite(gradient(0, 225, 950, H), text_layer(lines))
    ImageDraw.Draw(img).line([(W / 2 - 60, 1448), (W / 2 + 60, 1448)], fill=SOFT, width=2)
    if dealer:
        paste_logo(img, dealer, 1474 + (70 - dealer.height) // 2)
    img.save(tmp / "end.png")
    layers.append((tmp / "end.png", end["start"], None))
    return layers


def probe(src, entries, stream=None):
    cmd = ["ffprobe", "-v", "error"] + (["-select_streams", stream] if stream else [])
    return subprocess.check_output(cmd + ["-show_entries", entries, "-of", "csv=p=0", src]).decode().strip()


def compose(src, out, layers, music):
    dur = float(probe(src, "format=duration"))
    has_audio = bool(probe(src, "stream=index", "a"))
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", src]
    # Scale first so drafts and 720p clips get the same overlay layout as 1080p ones.
    chain, last = [f"[0:v]scale={W}:{H}:flags=lanczos[base]"], "base"
    for i, (png, start, stop) in enumerate(layers, 1):
        cmd += ["-loop", "1", "-t", f"{dur + 0.1:.2f}", "-i", str(png)]
        f = f"[{i}:v]format=rgba"
        if start is not None:
            f += f",fade=t=in:st={start}:d=0.4:alpha=1"
        if stop is not None:
            f += f",fade=t=out:st={stop}:d=0.4:alpha=1"
        chain += [f + f"[o{i}]", f"[{last}][o{i}]overlay[v{i}]"]
        last = f"v{i}"
    chain.append(f"[{last}]format=yuv420p[v]")

    audio = ["-map", "0:a?", "-c:a", "copy"]
    if music:
        m = len(layers) + 1
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        bed = f"[{m}:a]atrim=0:{dur:.2f},afade=t=out:st={dur - 0.8:.2f}:d=0.8"
        if has_audio:  # keep the clip's own sound effects on top of the music bed
            chain += [bed + ",volume=0.75[bed]", "[0:a]volume=1.0[sfx]",
                      "[sfx][bed]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]"]
        else:
            chain.append(bed + "[a]")
        audio = ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]

    cmd += ["-filter_complex", ";".join(chain), "-map", "[v]", *audio,
            "-c:v", "libx264", "-crf", "17", "-preset", "slow",
            "-t", f"{dur:.2f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--style", required=True, help="path to a styles/*.json file")
    ap.add_argument("--vehicle", required=True, help='e.g. "2027 Kia Telluride"')
    ap.add_argument("--out", required=True)
    ap.add_argument("--copy", help="per-car captions/headline JSON (overrides the style's wording)")
    ap.add_argument("--music", help="music bed file; default is music/<style>.m4a; 'none' to skip")
    ap.add_argument("--brand", default=str(SKILL / "brand.json"))
    a = ap.parse_args()
    style = json.loads(Path(a.style).read_text())
    brand = json.loads(Path(a.brand).read_text())
    copy = json.loads(Path(a.copy).read_text()) if a.copy else {}
    music = None
    if a.music != "none":
        music = Path(a.music) if a.music else SKILL / "music" / f"{style['name']}.m4a"
        music = music if music.exists() else None
    with tempfile.TemporaryDirectory() as d:
        compose(a.input, a.out, render(style, brand, a.vehicle, copy, Path(d)), music)
    print(a.out)
