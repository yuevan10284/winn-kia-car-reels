#!/usr/bin/env python3
"""Print a style's video prompt with the vehicle filled in.

  prompt.py heartfelt --vehicle "white 2027 Kia Telluride X-Line" \
            --look "glacial white pearl paint, black grille, black wheels, black roof rails"
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("style", help="heartfelt | sky-drop | exploded")
ap.add_argument("--vehicle", required=True)
ap.add_argument("--look", required=True, help="what makes this exact car recognisable, from the photos")
a = ap.parse_args()
style = json.loads((Path(__file__).resolve().parent.parent / "styles" / f"{a.style}.json").read_text())
print(style["prompt"].format(vehicle=a.vehicle, look=a.look))
