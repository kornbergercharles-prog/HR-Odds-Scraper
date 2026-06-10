import json
import asyncio
from playwright.async_api import async_playwright

print("DOWNLOADING LIVE DRAFTKINGS DATA...")

DK_URL = "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=player-props&subcategory=home-runs"

GET_TEXT_JS = """
    () => {
        function getTextFromNode(node) {
            let text = [];
            if (node.shadowRoot) {
                text = text.concat(getTextFromNode(node.shadowRoot));
            }
            for (let child of node.childNodes) {
                if (child.nodeType === 3) {
                    let t = child.textContent ? child.textContent.trim() : '';
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

SKIP_NAMES = {
    'batter props', 'pitcher props', 'game lines', 'aces', 'quick hits',
    'specials', 'series props', 'home runs', 'hits', 'total bases',
    'rbis', 'runs scored', 'stolen bases', 'sign up or log in',
    'draftkings', 'my bets', 'live in-game', 'rewards', 'how to bet',
    'more', 'vip', 'mlb', 'nfl', 'nba', 'nhl', 'futures', 'games',
    'quick sgp', 'bet slip', 'your picks will show up here', 'today',
    'tomorrow', 'sportsbook', 'baseball odds', 'mlb odds',
    'play free big league draw', 'opt in', 'join now', 'log in',
    'hits + runs + rbis', 'extra base hits', 'live batter props',
    'live pitcher props', 'at', 'sgp', 'more bets', 'draftkings social',
    'you must be logged in to view this content', 'nhl', 'wnba',
    'college baseball', 'boxing', 'popular', 'sport teams', 'a-z sports',
}

async def capture():
    results = []

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

        print("Loading DraftKings...")
        await page.goto(DK_URL, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(8)

        # Click Batter Props tab
        try:
            await page.click("text=BATTER PROPS")
            await asyncio.sleep(3)
            print("Clicked Batter Props")
        except Exception as e:
            print(f"Batter Props click failed: {e}")

        # Click Home Runs subcategory
        try:
            await page.click("text=HOME RUNS")
            await asyncio.sleep(3)
            print("Clicked Home Runs")
        except Exception as e:
            print(f"Home Runs click failed: {e}")

        # Scroll down to load all players
        print("Scrolling to load all players...")
        for i in range(10):
            await page.keyboard.press("End")
            await asyncio.sleep(1)

        await asyncio.sleep(3)

        print("Extracting odds...")
        all_text = await page.evaluate(GET_TEXT_JS)

        # The page shows: PlayerName, HR: N, [icon], 1+, +ODDS, 2+, >
        # We look for "1+" as the trigger then grab the next odds value
        found_one_plus = False
        last_name = None

        for i, t in enumerate(all_text):
            t = t.strip()
            if not t:
                continue

            # Detect player name — comes before "1+" marker
            is_name = (
                len(t) > 4 and
                len(t) < 40 and
                t[0].isupper() and
                ' ' in t and
                t.lower() not in SKIP_NAMES and
                not t.startswith('HR:') and
                not t.startswith('Today') and
                not t.startswith('Tomorrow')
            )

            is_odds = (t.startswith('+') or t.startswith('-')) and t[1:].isdigit()

            if is_name:
                last_name = t
                found_one_plus = False
            elif t == '1+':
                found_one_plus = True
            elif is_odds and found_one_plus and last_name:
                results.append({'player': last_name, 'dk_odds': t})
                found_one_plus = False
                last_name = None

        print(f"Found {len(results)} players")
        if results:
            print(f"Sample: {results[:5]}")

        await browser.close()

    with open("all_responses.json", "w", encoding="utf-8") as f:
        json.dump(results, f)
    print("Saved all_responses.json")

asyncio.run(capture())
