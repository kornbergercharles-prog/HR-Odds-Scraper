import requests
import json

print("DOWNLOADING LIVE DRAFTKINGS DATA...")

url = "https://sportsbook-nash.draftkings.com/sites/US-NY-SB/api/sportscontent/controldata/league/leagueSubcategory/v1/markets?isBatchable=false&templateVars=84240%2C17319&eventsQuery=%24filter%3DleagueId%20eq%20%2784240%27%20AND%20clientMetadata%2FSubcategories%2Fany%28s%3A%20s%2FId%20eq%20%2717319%27%29&marketsQuery=%24filter%3DclientMetadata%2FsubCategoryId%20eq%20%2717319%27%20AND%20tags%2Fall%28t%3A%20t%20ne%20%27SportcastBetBuilder%27%29&include=Events&entity=events"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("STATUS CODE:", response.status_code)

if response.status_code != 200:
    print("FAILED RESPONSE:")
    print(response.text[:1000])
    raise Exception(f"Bad status code: {response.status_code}")

data = response.json()

with open("all_responses.json", "w", encoding="utf-8") as f:
    json.dump(data, f)

print("Saved fresh all_responses.json")
