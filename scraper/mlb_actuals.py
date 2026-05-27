"""Fetch 2026 YTD actuals from MLB Stats API and normalize to engine schema."""
from __future__ import annotations

import json
from urllib.request import Request, urlopen

MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
USER_AGENT = "Mozilla/5.0"


def normalize_ip(ip_baseball: float) -> float:
    """Convert baseball IP notation (4.2 = 4 and 2/3) to true decimal (4.667)."""
    whole = int(ip_baseball)
    outs = round((ip_baseball - whole) * 10)
    return whole + outs / 3


def normalize_hitter(entry: dict, as_of: str) -> dict:
    """Convert an MLB Stats API hitter record to engine schema."""
    player = entry["player"]
    s = entry["stat"]
    team = entry.get("team", {}).get("abbreviation", "")
    mlbam_id = str(player["id"])

    doubles = int(s.get("doubles", 0))
    triples = int(s.get("triples", 0))
    hr = int(s.get("homeRuns", 0))
    h = int(s.get("hits", 0))
    singles = h - doubles - triples - hr
    tb = singles + 2 * doubles + 3 * triples + 4 * hr
    sb = int(s.get("stolenBases", 0))
    cs = int(s.get("caughtStealing", 0))
    bb = int(s.get("baseOnBalls", 0))
    hbp = int(s.get("hitByPitch", 0))
    sf = int(s.get("sacFlies", 0))
    ab = int(s.get("atBats", 0))

    stats = {
        "PA": int(s.get("plateAppearances", 0)),
        "AB": ab, "H": h, "HR": hr,
        "R": int(s.get("runs", 0)), "RBI": int(s.get("rbi", 0)),
        "SB": sb, "CS": cs, "BB": bb, "SO": int(s.get("strikeOuts", 0)),
        "HBP": hbp, "SF": sf,
        "1B": singles, "2B": doubles, "3B": triples,
        "G": int(s.get("gamesPlayed", 0)),
        "TB": tb, "NSB": sb - cs,
    }

    pa_denom = ab + bb + hbp + sf
    stats["AVG"] = round(h / ab, 3) if ab > 0 else 0.0
    obp_num = h + bb + hbp
    stats["OBP"] = round(obp_num / pa_denom, 3) if pa_denom > 0 else 0.0
    stats["SLG"] = round(tb / ab, 3) if ab > 0 else 0.0
    stats["OPS"] = round(stats["OBP"] + stats["SLG"], 3)

    return {
        "id": f"mlbam_{mlbam_id}_H",
        "name": player["fullName"],
        "pool": "hitter",
        "positions": [],
        "team": team,
        "stats": stats,
        "metadata": {
            "mlbam_id": mlbam_id,
            "base_id": f"mlbam_{mlbam_id}",
            "source": "mlb_stats_api",
            "as_of": as_of,
        },
    }


def normalize_pitcher(entry: dict, qs: int, as_of: str) -> dict:
    """Convert an MLB Stats API pitcher record to engine schema."""
    player = entry["player"]
    s = entry["stat"]
    team = entry.get("team", {}).get("abbreviation", "")
    mlbam_id = str(player["id"])

    ip = normalize_ip(float(s.get("inningsPitched", "0")))
    gs = int(s.get("gamesStarted", 0))
    sv = int(s.get("saves", 0))
    hld = int(s.get("holds", 0))
    k = int(s.get("strikeOuts", 0))
    bb = int(s.get("baseOnBalls", 0))
    er = int(s.get("earnedRuns", 0))
    h_allowed = int(s.get("hits", 0))

    pool = "starter" if gs > 0 else "reliever"
    positions = []
    if gs > 0:
        positions.append("SP")
    if sv > 0 or hld > 0 or gs == 0:
        positions.append("RP")
    if not positions:
        positions.append("SP")

    stats = {
        "IP": round(ip, 4), "ER": er, "BB": bb, "H_ALLOWED": h_allowed,
        "K": k, "W": int(s.get("wins", 0)), "L": int(s.get("losses", 0)),
        "SV": sv, "HLD": hld, "GS": gs,
        "G": int(s.get("gamesPitched", 0)),
        "QS": qs, "SV_HLD": sv + hld,
    }

    stats["ERA"] = round(9 * er / ip, 2) if ip > 0 else 0.0
    stats["WHIP"] = round((bb + h_allowed) / ip, 2) if ip > 0 else 0.0
    stats["K_BB"] = round(k / bb, 2) if bb > 0 else 0.0
    stats["K_9"] = round(9 * k / ip, 2) if ip > 0 else 0.0
    stats["BB_9"] = round(9 * bb / ip, 2) if ip > 0 else 0.0

    return {
        "id": f"mlbam_{mlbam_id}_P",
        "name": player["fullName"],
        "pool": pool,
        "positions": positions,
        "team": team,
        "stats": stats,
        "metadata": {
            "mlbam_id": mlbam_id,
            "base_id": f"mlbam_{mlbam_id}",
            "source": "mlb_stats_api",
            "as_of": as_of,
        },
    }


def derive_qs_from_games(games: list[dict]) -> int:
    """Count quality starts from game log entries."""
    qs = 0
    for game in games:
        s = game["stat"]
        if int(s.get("gamesStarted", 0)) == 0:
            continue
        ip = normalize_ip(float(s.get("inningsPitched", "0")))
        er = int(s.get("earnedRuns", 0))
        if ip >= 6.0 and er <= 3:
            qs += 1
    return qs


def _fetch_json(url: str) -> dict:
    """Fetch JSON from a URL."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_actuals(season: int = 2026) -> dict[str, list[dict]]:
    """Fetch YTD hitter and pitcher actuals from MLB Stats API.

    Returns {"hitters": [...], "pitchers": [...]} with raw API records.
    Raises on any fetch failure.
    """
    base = f"{MLB_API_BASE}/stats?stats=season&season={season}&sportId=1&limit=5000&playerPool=ALL"
    hitters = _fetch_json(f"{base}&group=hitting")["stats"][0]["splits"]
    pitchers = _fetch_json(f"{base}&group=pitching")["stats"][0]["splits"]
    return {"hitters": hitters, "pitchers": pitchers}


def fetch_qs(pitchers: list[dict], season: int = 2026) -> dict[str, int]:
    """Derive QS from game logs for all pitchers with starts.

    Returns {mlbam_id_str: qs_count}. Raises on any game log fetch failure.
    """
    qs_map: dict[str, int] = {}
    for p in pitchers:
        gs = int(p["stat"].get("gamesStarted", 0))
        mlbam_id = str(p["player"]["id"])
        if gs == 0:
            qs_map[mlbam_id] = 0
            continue
        url = f"{MLB_API_BASE}/people/{mlbam_id}/stats?stats=gameLog&group=pitching&season={season}&gameType=R"
        gl_data = _fetch_json(url)
        games = gl_data["stats"][0]["splits"]
        qs_map[mlbam_id] = derive_qs_from_games(games)
    return qs_map


def build_actuals(season: int = 2026, as_of: str = "") -> list[dict]:
    """Full pipeline: fetch actuals + QS, normalize, return player list."""
    if not as_of:
        from datetime import date
        as_of = date.today().isoformat()

    raw = fetch_actuals(season)
    qs_map = fetch_qs(raw["pitchers"], season)

    players = []
    for entry in raw["hitters"]:
        players.append(normalize_hitter(entry, as_of))
    for entry in raw["pitchers"]:
        mlbam_id = str(entry["player"]["id"])
        qs = qs_map.get(mlbam_id, 0)
        players.append(normalize_pitcher(entry, qs=qs, as_of=as_of))

    return players
