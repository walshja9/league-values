"""Orchestrator: fetch projections, blend, write output."""
from __future__ import annotations

import json
import os

from .fangraphs import fetch_all, save_raw
from .blend import blend_projections


DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "projections", "current.json")
DEFAULT_RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "projections", "raw")


def refresh(
    output_path: str = DEFAULT_OUTPUT,
    raw_dir: str = DEFAULT_RAW_DIR,
    delay: float = 1.0,
) -> list[dict]:
    print("Fetching projections from FanGraphs...")
    raw = fetch_all(delay=delay)

    for key, players in raw.items():
        print(f"  {key}: {len(players)} players")

    print("Saving raw data...")
    save_raw(raw, raw_dir)

    print("Blending projections...")
    blended = blend_projections(raw)
    print(f"  {len(blended)} total players")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(blended, f, indent=2)
    print(f"Written to {output_path}")

    return blended


if __name__ == "__main__":
    refresh()
