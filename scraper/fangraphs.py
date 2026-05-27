"""Fetch Steamer Rest-of-Season projections from the FanGraphs API."""
from __future__ import annotations

import json
import os
import time
from urllib.request import Request, urlopen

PROJECTION_URL = "https://www.fangraphs.com/api/projections"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_projections(system: str, stats: str) -> list[dict]:
    url = f"{PROJECTION_URL}?type={system}&stats={stats}&pos=all&team=0&players=0&lg=all"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all(delay: float = 1.0) -> dict[str, list[dict]]:
    sets = [
        ("steamer_hitters", "steamerr", "bat"),
        ("steamer_pitchers", "steamerr", "pit"),
    ]
    result = {}
    for i, (key, system, stats) in enumerate(sets):
        result[key] = fetch_projections(system, stats)
        if delay > 0 and i < len(sets) - 1:
            time.sleep(delay)
    return result


def save_raw(data: dict[str, list[dict]], output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    for key, players in data.items():
        path = os.path.join(output_dir, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(players, f, indent=2)
