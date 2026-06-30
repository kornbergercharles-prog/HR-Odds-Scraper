import json
import asyncio
from playwright.async_api import async_playwright

print("DOWNLOADING LIVE BET365 DATA...")

BET365_URL = "https://nj.bet365.com/#/AC/B16/C20525425/D43/E163118/F43/N0/"

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
    'all sports', 'live', 'casino', 'promos', 'join', 'log in',
    'lines', 'sgp +', 'bet boost', 'props', 'futures', 'all',
    'game lines', 'hits', 'pitcher strikeouts', 'home runs',
    'total bases', 'alternative game total', 'alternative run line',
    'a run in the 1st inning', 'player / last 5', 'trending',
    'civ v nor', 'world cup 2026', 'mlb', 'wnba', 'wimbledon',
    'pga tour', 'wc26 challenge', 'most used', 'responsible gaming',
    'if you or someone you know has a gambling problem and wants help',
    'call 1-800 gambler', 'bet365',
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

        print("Loading bet365...")
        try:
            await page.goto(BET365_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Page load failed: {e}")
            await browser.close()
            with open("bet365_responses.json", "w", encoding="utf-8") as f:
                json.dump([], f)
            return

        page_text = await page.inner_text("body")
        if "home runs" not in page_text.lower():
            print("Home Runs section not found — saving empty data")
            await browser.close()
            with open("bet365_responses.json", "w", encoding="utf-8") as f:
                json.dump([], f)
            return

        print("Scrolling to load all games/players...")
        for i in range(15):
            await page.keyboard.press("End")
            await asyncio.sleep(1)

        await asyncio.sleep(3)
        await page.screenshot(path="bet365_screenshot.png")
        print("Screenshot saved")

        print("Extracting odds...")
        all_text = await page.evaluate(GET_TEXT_JS)

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
                results.append({"player": last_name, "bet365_odds": t})
                last_name = None

        seen = set()
        deduped = []
        for r in results:
            if r["player"] not in seen:
                seen.add(r["player"])
                deduped.append(r)

        print(f"Found {len(deduped)} players")
        if deduped:
            print(f"Sample: {deduped[:5]}")

        await browser.close()

    with open("bet365_responses.json", "w", encoding="utf-8") as f:
        json.dump(deduped, f)
    print(f"Saved bet365_responses.json ({len(deduped)} players)")

asyncio.run(capture())
