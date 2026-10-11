#!/usr/bin/env python3
"""Burn Winn Kia branding, captions and an end card onto a raw generated clip.

  brand_video.py --input raw.mp4 --style ../styles/heartfelt.json \
                 --vehicle "2027 Kia Telluride" --out final.mp4

Text is rendered with Pillow (the local ffmpeg has no drawtext filter) and
composited with ffmpeg overlay + alpha fades. Captions and timings come from the
style JSON; the dealer name and address come from brand.json.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONT = "/System/Library/Fonts/Avenir Next.ttc"
BOLD, DEMI, MEDIUM = 0, 2, 5
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
            ImageDraw.Draw(shadow).text((x, y + 3), c, font=f, fill=(0, 0, 0, 200))
            ImageDraw.Draw(layer).text((x, y), c, font=f, fill=fill)
            x += w
    return Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(8)), layer)


def rule(img, y):
    ImageDraw.Draw(img).line([(W / 2 - 60, y), (W / 2 + 60, y)], fill=SOFT, width=2)


def render(style, brand, vehicle, tmp):
    """Write overlay PNGs; return [(path, fade_in_at, fade_out_at or None)]."""
    layers = []
    fill = lambda t: t.format(vehicle=vehicle, VEHICLE=vehicle.upper())

    # Persistent wordmark, kept below the Reels/TikTok top UI zone.
    top, sub = brand["wordmark"]
    img = Image.alpha_composite(
        gradient(150, 0, 0, 520),
        text_layer([(top, font(58, BOLD), 232, WHITE, 14), (sub, font(26, DEMI), 312, SOFT, 12)]),
    )
    rule(img, 366)
    img.save(tmp / "brand.png")
    layers.append((tmp / "brand.png", 0.2, None))

    # Story captions, kept above the bottom UI zone.
    base = gradient(0, 170, 1150, H)
    for i, cap in enumerate(style["captions"]):
        texts = [fill(t) for t in cap["lines"]]
        y0 = 1400 - (len(texts) - 1) * 42
        lines = [(t, fit(t, 64, DEMI), y0 + j * 84, WHITE, 0) for j, t in enumerate(texts)]
        p = tmp / f"cap{i}.png"
        Image.alpha_composite(base, text_layer(lines)).save(p)
        layers.append((p, cap["start"], cap["end"]))

    # End card: kicker, headline, dealer name, address.
    end = style["end_card"]
    kicker = fill(end["kicker"])
    head = [fill(t) for t in end["headline"]]
    y = 1262 - (len(head) - 2) * 84
    lines = [(kicker, fit(kicker, 34, DEMI, 8), y - 62, SOFT, 8)]
    lines += [(t, fit(t, 68, DEMI), y + j * 84, WHITE, 0) for j, t in enumerate(head)]
    lines += [
        (brand["name"], font(44, BOLD), 1474, WHITE, 0),
        (brand["address"], fit(brand["address"], 36, MEDIUM), 1536, SOFT, 0),
    ]
    img = Image.alpha_composite(gradient(0, 215, 950, H), text_layer(lines))
    rule(img, 1450)
    img.save(tmp / "end.png")
    layers.append((tmp / "end.png", end["start"], None))
    return layers


def compose(src, out, layers):
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", src]
    chain, last = [], "0:v"
    for i, (png, start, stop) in enumerate(layers, 1):
        cmd += ["-loop", "1", "-t", f"{dur + 0.1:.2f}", "-i", str(png)]
        f = f"[{i}:v]format=rgba,fade=t=in:st={start}:d=0.4:alpha=1"
        if stop is not None:
            f += f",fade=t=out:st={stop}:d=0.4:alpha=1"
        chain.append(f + f"[o{i}]")
        chain.append(f"[{last}][o{i}]overlay[v{i}]")
        last = f"v{i}"
    chain.append(f"[{last}]scale={W}:{H},format=yuv420p[v]")
    cmd += ["-filter_complex", ";".join(chain), "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-c:a", "copy",
            "-t", f"{dur:.2f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--style", required=True, help="path to a styles/*.json file")
    ap.add_argument("--vehicle", required=True, help='e.g. "2027 Kia Telluride"')
    ap.add_argument("--out", required=True)
    ap.add_argument("--brand", default=str(SKILL / "brand.json"))
    a = ap.parse_args()
    style = json.loads(Path(a.style).read_text())
    brand = json.loads(Path(a.brand).read_text())
    with tempfile.TemporaryDirectory() as d:
        compose(a.input, a.out, render(style, brand, a.vehicle, Path(d)))
    print(a.out)
