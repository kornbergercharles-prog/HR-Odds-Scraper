import json
import asyncio
from playwright.async_api import async_playwright

print("DOWNLOADING LIVE DRAFTKINGS DATA...")

DK_URL = "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=player-props&subcategory=home-runs"

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

        print("Clicking Batter Props tab...")
        try:
            await page.click("text=BATTER PROPS")
            await asyncio.sleep(3)
            print("Clicked Batter Props")
        except Exception as e:
            print(f"Could not click Batter Props: {e}")

        print("Looking for Home Runs section...")
        try:
            await page.click("text=Home Runs")
            await asyncio.sleep(3)
            print("Clicked Home Runs")
        except Exception as e:
            print(f"Could not click Home Runs: {e}")

        await page.screenshot(path="dk_screenshot.png")
        print("Screenshot saved")

        print("Extracting odds...")
        js_code = """
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

        all_text = await page.evaluate(js_code)

        skip_names = new Set([
            'BATTER PROPS', 'PITCHER PROPS', 'GAME LINES', 'ACES', 'QUICK HITS',
            'SPECIALS', 'SERIES PROPS', 'Home Runs', 'Hits', 'Total Bases',
            'RBIs', 'Runs Scored', 'Stolen Bases', 'Sign Up or Log In',
            'DraftKings', 'My Bets', 'Live In-Game', 'Rewards', 'How to Bet',
            'More', 'VIP', 'MLB', 'NFL', 'NBA', 'NHL', 'Futures', 'Games',
            'Quick SGP', 'Specials', 'BET SLIP', 'YOUR PICKS WILL SHOW UP HERE'
        ])

        last_name = None
        for t in all_text:
            t = t.strip()
            if not t:
                continue
            is_odds = (t.startswith('+') or t.startswith('-')) and t[1:].isdigit()
            is_name = (
                len(t) > 4 and
                len(t) < 40 and
                t[0].isupper() and
                ' ' in t and
                t not in skip_names
            )
            if is_name:
                last_name = t
            elif is_odds and last_name:
                results.append({'player': last_name, 'dk_odds': t})
                last_name = None

        print(f"Found {len(results)} players")
        if results:
            print(f"Sample: {results[:3]}")

        await browser.close()

    with open("all_responses.json", "w", encoding="utf-8") as f:
        json.dump(results, f)
    print("Saved all_responses.json")

asyncio.run(capture())
