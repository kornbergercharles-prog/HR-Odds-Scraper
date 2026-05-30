import json
import pandas as pd
from openpyxl.styles import PatternFill, Font, Alignment
from difflib import SequenceMatcher

print("SCRIPT STARTED")


def clean(x):
    if not x:
        return ""
    return (
        str(x)
        .replace("\xa0", " ")
        .replace(".", "")
        .replace("\n", " ")
        .strip()
        .lower()
    )


def implied_prob(odds):
    try:
        s = str(odds).strip()
        o = int(s.replace("+", ""))
        if s.startswith("-"):
            return (-o) / ((-o) + 100)
        else:
            return 100 / (o + 100)
    except Exception:
        return None


def fmt_prob(val):
    return f"{val:.1%}" if val is not None else ""


def get_player_name_dk(m):
    if not isinstance(m, dict):
        return None
    if m.get("label") == "1+":
        participants = m.get("participants")
        if isinstance(participants, list) and participants:
            name = participants[0].get("name")
            if name:
                return name
    if "name" in m:
        return m.get("name")
    if "displayName" in m:
        return m.get("displayName")
    if "outcomes" in m and isinstance(m["outcomes"], list):
        if m["outcomes"]:
            return m["outcomes"][0].get("label")
    return None


def parse_dk():
    with open("all_responses.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    rows = []

    def extract(market_list):
        for m in market_list:
            try:
                if not isinstance(m, dict):
                    continue
                if m.get("label") != "1+":
                    continue
                player = get_player_name_dk(m)
                if not player:
                    continue
                rows.append({
                    "player": player,
                    "dk_odds": m.get("displayOdds", {}).get("american"),
                })
            except Exception:
                continue

    def find(obj):
        if isinstance(obj, list):
            extract(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    find(v)

    find(raw)
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["player", "dk_odds"])
    df = df.drop_duplicates(subset=["player"])
    print(f"DraftKings players found: {len(df)}")
    return df


def parse_fanduel():
    try:
        with open("fanduel_responses.json", "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        print("WARNING: fanduel_responses.json not found — skipping FanDuel data.")
        return pd.DataFrame(columns=["player", "fd_odds"])

    df = pd.DataFrame(raw)
    df = df.dropna(subset=["player", "fd_odds"])
    df = df.drop_duplicates(subset=["player"])
    print(f"FanDuel players found: {len(df)}")
    return df


def fuzzy_match_names(dk_name, fd_names, threshold=0.8):
    """Find best match for a DK name in FanDuel names list"""
    dk_clean = clean(dk_name)
