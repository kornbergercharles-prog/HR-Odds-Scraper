import requests
import json

print("DOWNLOADING LIVE DRAFTKINGS DATA...")

url = "https://sportsbook-nash.draftkings.com/sites/US-NY-SB/api/sportscontent/controldata/league/leagueSubcategory/v1/markets"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://sportsbook.draftkings.com/",
    "Origin": "https://sportsbook.draftkings.com",
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"STATUS CODE: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        with open("all_responses.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
        print("DraftKings data saved")
    else:
        print(f"DraftKings blocked — saving empty data")
        with open("all_responses.json", "w", encoding="utf-8") as f:
            json.dump({}, f)
except Exception as e:
    print(f"Error: {e}")
    with open("all_responses.json", "w", encoding="utf-8") as f:
        json.dump({}, f)
