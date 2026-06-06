import json
import asyncio
from playwright.async_api import async_playwright

print("DOWNLOADING LIVE FANDUEL DATA...")

TARGET_URL = "https://sportsbook.fanduel.com/navigation/mlb?tab=parlay-builder"
PLAYER_PROPS_URL = "https://sportsbook.fanduel.com/navigation/mlb?tab=player-props"

SKIP_NAMES = {
    "fanduel sportsbook", "my bets", "log in", "join now", "live now",
    "french open", "pga tour", "parlay hub", "popular bets", "learn to bet",
    "free to play", "all sports", "aussie rules", "rugby league", "rugby union",
    "other links", "nfl team odds", "nba team odds", "mlb team odds",
    "ncaaf team odds", "ncaab team odds", "terms and conditions",
    "responsible gaming", "house rules", "in person sportsbook",
    "mlb: parlay builder betting odds", "more info", "log in", "play free",
    "open your locker", "parlay builder", "futures sgp", "world series",
    "league winners", "win totals", "home runs", "mlb parlay builders",
    "to hit a home run parlay builder", "to hit a home run",
    "to record a hit parlay builder", "to record 2+ hits parlay builder",
    "to record 3+ hits  parlay builder", "to record an rbi parlay builder",
    "to record 2+ rbis parlay builder", "sportsbook odds", "mlb odds",
    "parlay builder", "mlb odds", "choose your bet type:", "select your bets:",
    "determine your stake:", "calculate potential winnings:", "verifying location…",
    "more wagers", "show less", "show more", "back to top", "betslip empty",
    "add selections to place bet", "fanduel group sites", "fanduel fantasy",
    "fanduel racing", "fanduel research", "fanduel tv", "fanduel faceoff",
    "fanduel apps", "fantasy (ios)", "fantasy (android)", "sportsbook (ios)",
    "sportsbook (android)", "nfl odds", "nba odds", "nhl odds",
    "college football odds", "college basketball odds", "soccer odds",
    "golf odds", "ufc odds", "nascar and f1 odds", "tennis odds",
    "boxing odds", "wnba odds", "follow fanduel", "privacy policy",
    "terms of use", "press & media", "about us", "how to bet",
    "california privacy rights", "your privacy choices", "games",
    "sportsbook odds", "baseball", "basketball", "boxing", "cricket",
    "cycling", "darts", "football", "golf", "lacrosse", "mma", "motorsport",
    "rugby league", "rugby union", "soccer", "tennis",
    "awards", "playoffs", "player props", "mlb player props",
    "to record a hit", "to record an rbi", "daily dinger",
    "play free for a shot at a profit boost"
}

SHADOW_CLICK_JS = """
    (searchText) => {
        function findAndClick(root) {
            let children = root.querySelectorAll ? Array.from(root.querySelectorAll('*')) : [];
            for (let el of children) {
                if (el.shadowRoot) {
                    let result = findAndClick(el.shadowRoot);
                    if (result) return true;
                }
                let text = el.textContent.trim();
                if (text === searchText || text.toLowerCase() === searchText.toLowerCase()) {
                    el.click();
                    return true;
                }
            }
            return false;
        }
        return findAndClick(document.body);
    }
"""

GET_TEXT_JS = """
    () => {
        function getTextFromNode(node) {
            let text = [];
            if (node.shadowRoot) {
                text = text.concat(getTextFromNode(node.shadowRoot));
            }
            for (let child of node.childNodes) {
                if (child.nodeType === 3) {
                    let t = child.textContent.trim();
                    if (t) text.push(t);
                } else if (child.nodeType === 1) {
                    text = text.concat(getTextFromNode(child));
                }
            }
            return text;
        }
        return getTextFromNode(document.body);
    }
"""

def extract_odds_from_text(all_text):
    results = []
    last_name = None
    for t in all_text:
        t = t.strip()
        if not t:
            continue
        is_odds = (t.startswith("+") or t.startswith("-")) and t[1:].isdigit()
        is_name = (
            len(t) > 4 and
            len(t) < 40 and
            t[0].isupper() and
            " " in t and
            t.lower() not in SKIP_NAMES
        )
        if is_name:
            last_name = t
        elif is_odds and last_name:
            results.append({"player": last_name, "fd_odds": t})
            last_name = None
    return results

def deduplicate(results):
    seen = set()
    deduped = []
    for r in results:
        if r["player"] not in seen:
            seen.add(r["player"])
            deduped.append(r)
    return deduped

def looks_like_hr_odds(results):
    if not results:
        return False
    positive = sum(1 for r in results if r["fd_odds"].startswith("+"))
    total = len(results)
    ratio = positive / total
    print(f"Positive odds ratio: {positive}/{total} = {ratio:.0%}")
    return ratio >= 0.7

async def scrape_parlay_builder(page):
    print("Trying Parlay Builder tab...")
    await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(10)

    page_text = await page.inner_text("body")
    if "parlay builder" not in page_text.lower():
        print("Parlay Builder not found — skipping")
        return []

    try:
        hr = page.get_by_text("To Hit a Home Run Parlay Builder", exact=False)
        await hr.first.click()
        print("Clicked HR section")
    except Exception as e:
        print(f"Click failed: {e}")
        return []

    await asyncio.sleep(8)

    clicked = 0
    while True:
        try:
            show_more = page.get_by_text("Show more", exact=False).first
            await show_more.wait_for(timeout=3000)
            await show_more.click()
            clicked += 1
            await asyncio.sleep(2)
        except Exception:
            break
    print(f"Clicked Show more {clicked} times")

    await asyncio.sleep(5)
    all_text = await page.evaluate(GET_TEXT_JS)
    results = extract_odds_from_text(all_text)

    if not looks_like_hr_odds(results):
        print("Results don't look like HR odds — falling back")
        return []

    return results

async def scrape_player_props(page):
    print("Trying Player Props — expanding To Hit A Home Run dropdown...")
    await page.goto(PLAYER_PROPS_URL, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(15)

    print("Attempting shadow DOM click on To Hit A Home Run...")
    clicked = await page.evaluate(SHADOW_CLICK_JS, "To Hit A Home Run")
    if clicked:
        print("Shadow DOM click succeeded")
    else:
        print("Shadow DOM click failed — trying partial match...")
        clicked = await page.evaluate("""
            () => {
                function findAndClick(root) {
                    let children = root.querySelectorAll ? Array.from(root.querySelectorAll('*')) : [];
                    for (let el of children) {
                        if (el.shadowRoot) {
                            let result = findAndClick(el.shadowRoot);
                            if (result) return true;
                        }
                        let text = el.textContent.trim().toLowerCase();
                        if (text.includes('to hit a home run') && text.length < 30) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
                return findAndClick(document.body);
            }
        """)
        print(f"Partial match click: {clicked}")

    await asyncio.sleep(8)

    all_text = await page.evaluate(GET_TEXT_JS)
    results = extract_odds_from_text(all_text)
    print(f"Player Props found {len(results)} players")

    if results:
        print(f"Sample: {results[:3]}")

    return results

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        results = await scrape_parlay_builder(page)

        if not results:
            print("Falling back to Player Props...")
            results = await scrape_player_props(page)

        await browser.close()

    if not results:
        print("WARNING: No FanDuel HR odds found from either source.")
        with open("fanduel_responses.json", "w", encoding="utf-8") as f:
            json.dump([], f)
    else:
        deduped = deduplicate(results)
        with open("fanduel_responses.json", "w", encoding="utf-8") as f:
            json.dump(deduped, f)
        print(f"Saved fanduel_responses.json ({len(deduped)} players)")

asyncio.run(capture())
