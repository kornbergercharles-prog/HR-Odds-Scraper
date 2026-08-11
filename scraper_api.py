import requests
import json
import os

print("DOWNLOADING FANDUEL + BOVADA DATA VIA ODDS API...")

API_KEY = os.getenv("ODDS_API_KEY")
SPORT = "baseball_mlb"
REGIONS = "us"
MARKET = "batter_home_runs_alternate"
ODDS_FORMAT = "american"

# Step 1: Get all today's events
events_url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/"
params = {"apiKey": API_KEY}

try:
    events_resp = requests.get(events_url, params=params, timeout=30)
    print(f"Events status: {events_resp.status_code}")
    print(f"Requests remaining: {events_resp.headers.get('x-requests-remaining')}")
    events = events_resp.json()
    print(f"Games today: {len(events)}")
except Exception as e:
    print(f"Events fetch failed: {e}")
    with open("odds_api_responses.json", "w") as f:
        json.dump([], f)
    exit()

# Step 2: Pull HR odds for each game
all_results = []

for event in events:
    event_id = event["id"]
    home = event["home_team"]
    away = event["away_team"]
    print(f"Fetching: {away} @ {home}...")

    odds_url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKET,
        "oddsFormat": ODDS_FORMAT,
    }

    try:
        resp = requests.get(odds_url, params=params, timeout=30)
        print(f"  Status: {resp.status_code} | Remaining: {resp.headers.get('x-requests-remaining')}")

        if resp.status_code != 200:
            print(f"  Skipping: {resp.text[:100]}")
            continue

        data = resp.json()

        for bookmaker in data.get("bookmakers", []):
            book_key = bookmaker["key"]
            book_title = bookmaker["title"]

            # Only keep FanDuel and Bovada
            if book_key not in ["fanduel", "bovada"]:
                continue

            for market in bookmaker.get("markets", []):
                if market["key"] != MARKET:
                    continue

                for outcome in market.get("outcomes", []):
                    point = outcome.get("point")
                    # Only keep 0.5 point = 1+ HR
                    if point != 0.5:
                        continue

                    player = outcome.get("description") or outcome.get("name")
                    price = outcome.get("price")

                    if player and price:
                        all_results.append({
                            "player": player,
                            "book": book_title,
                            "book_key": book_key,
                            "odds": price,
                        })

    except Exception as e:
        print(f"  Error: {e}")
        continue

print(f"\nTotal entries found: {len(all_results)}")
if all_results:
    print(f"Sample: {all_results[:3]}")

with open("odds_api_responses.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2)
print("Saved odds_api_responses.json")
