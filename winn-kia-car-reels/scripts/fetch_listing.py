#!/usr/bin/env python3
"""Pull a vehicle's photos and basic facts from the Winn Kia of Fremont website.

  fetch_listing.py --list telluride            # print new-inventory listing URLs for a model
  fetch_listing.py <listing-url> --out <dir>   # download photos + listing.json + contact sheet
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

SITE = "https://www.winnkiaoffremont.com"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126 Safari/537.36"
)
PHOTO_RE = re.compile(r"content\.homenetiol\.com/(\d+/\d+)/[0-9x]+/([a-f0-9]+)\.jpg")
PHOTO_SIZE = "1920x1440"


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def list_model(model, condition):
    html = get(f"{SITE}/inventory/{condition}/kia/{model.lower().replace(' ', '-')}")
    seen = []
    for path in re.findall(rf"viewdetails/{condition}/[a-z0-9]+/[a-z0-9-]+", html):
        if path not in seen:
            seen.append(path)
    for path in seen:
        print(f"{SITE}/{path}")
    if not seen:
        sys.exit(f"No {condition} listings found for '{model}'.")


def fetch(url, out, max_photos):
    html = get(url)
    out = Path(out)
    photos_dir = out / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)

    # Page <title>: "New <Color> <Year> Kia <Model Trim> for Sale in Newark, CA | <VIN> | Winn Kia of Fremont"
    title = re.search(r"<title>([^<]*)", html)
    title = title.group(1).strip() if title else ""
    head = title.split("|")[0].strip()
    m = re.match(r"(New|Used|Certified[\w\s-]*?)\s+(.*?)\s+((?:19|20)\d{2})\s+(.*?)\s+for Sale", head, re.I)
    info = {"url": url, "page_title": title}
    if m:
        info.update(
            condition=m.group(1), color=m.group(2), year=m.group(3), model_trim=m.group(4),
            vehicle=f"{m.group(3)} {' '.join(m.group(4).split()[:2])}",
        )
    vin = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", title)
    if vin:
        info["vin"] = vin.group(1)
    stock = re.search(r"stockNumber\s*=\s*['\"]([^'\"]+)|\"sku\":\s*\"([^\"]+)", html)
    if stock:
        info["stock"] = stock.group(1) or stock.group(2)

    ids = []
    for prefix, pid in PHOTO_RE.findall(html):
        if (prefix, pid) not in ids:
            ids.append((prefix, pid))
    if not ids:
        sys.exit("No photos found on that page. Is it a vehicle detail (viewdetails) URL?")
    for i, (prefix, pid) in enumerate(ids[:max_photos], 1):
        data = get(f"https://content.homenetiol.com/{prefix}/{PHOTO_SIZE}/{pid}.jpg", binary=True)
        (photos_dir / f"{i:02d}.jpg").write_bytes(data)
    info["photo_count"] = min(len(ids), max_photos)
    (out / "listing.json").write_text(json.dumps(info, indent=2))

    # Contact sheet so the photos can be reviewed in one look.
    cols = 5
    rows = -(-info["photo_count"] // cols)
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-pattern_type", "glob", "-i", str(photos_dir / "*.jpg"),
         "-vf", f"scale=384:256,tile={cols}x{rows}", "-frames:v", "1", str(out / "contact-sheet.jpg")],
        check=False,
    )
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--list", metavar="MODEL")
    ap.add_argument("--condition", default="new", choices=["new", "used"])
    ap.add_argument("--out", default=".")
    ap.add_argument("--max-photos", type=int, default=20)
    a = ap.parse_args()
    if a.list:
        list_model(a.list, a.condition)
    elif a.url:
        fetch(a.url, a.out, a.max_photos)
    else:
        ap.error("give a listing URL or --list MODEL")
