import json
import pandas as pd
from openpyxl.styles import PatternFill, Font, Alignment

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
        print("WARNING: fanduel_responses.json not found")
        return pd.DataFrame(columns=["player", "fd_odds"])

    df = pd.DataFrame(raw)
    df = df.dropna(subset=["player", "fd_odds"])
    df = df.drop_duplicates(subset=["player"])
    print(f"FanDuel players found: {len(df)}")
    return df


# Read watchlist
with open("watchlist.txt", "r", encoding="utf-8") as f:
    watchlist_raw = [line.strip() for line in f if line.strip()]

watchlist = set(clean(x) for x in watchlist_raw)

# Parse both books
dk_df = parse_dk()
fd_df = parse_fanduel()

# Simple full outer join - keep ALL players from both books
df = dk_df.merge(fd_df, on="player", how="outer")

# Calculate implied probabilities
df["dk_implied"] = df["dk_odds"].apply(implied_prob)
df["fd_implied"] = df["fd_odds"].apply(implied_prob)
df["avg_implied"] = df[["dk_implied", "fd_implied"]].mean(axis=1)
df = df.sort_values("avg_implied", ascending=False, na_position="last")

# Build output
out = pd.DataFrame({
    "Player":           df["player"],
    "DK Odds":          df["dk_odds"].fillna("—"),
    "DK Impl. Prob":    df["dk_implied"].apply(fmt_prob),
    "FanDuel Odds":     df["fd_odds"].fillna("—"),
    "FD Impl. Prob":    df["fd_implied"].apply(fmt_prob),
    "Avg Impl. Prob":   df["avg_implied"].apply(fmt_prob),
})

yellow      = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
dark_blue   = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF", name="Arial", size=10)
cell_font   = Font(name="Arial", size=10)
center      = Alignment(horizontal="center")

with pd.ExcelWriter("hr_odds.xlsx", engine="openpyxl") as writer:
    out.to_excel(writer, index=False, sheet_name="HR Odds")
    ws = writer.sheets["HR Odds"]

    for cell in ws[1]:
        cell.fill      = dark_blue
        cell.font      = header_font
        cell.alignment = center

    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    matched = 0
    for row_idx in range(2, ws.max_row + 1):
        is_watch = clean(ws.cell(row=row_idx, column=1).value) in watchlist
        if is_watch:
            matched += 1
        for col_idx in range(1, ws.max_column + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font      = cell_font
            cell.alignment = center
            if is_watch:
                cell.fill = yellow

print(f"Saved hr_odds.xlsx with {len(out)} players")
print(f"Watchlist matches: {matched}")
