import json
import asyncio
from playwright.async_api import async_playwright

print("DOWNLOADING LIVE DRAFTKINGS DATA...")

DK_URL = "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=player-props&subcategory=home-runs"

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

        print("Loading DraftKings...")
        await page.goto(DK_URL, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)

        page_text = await page.inner_text("body")
        print(f"Page text sample:\n{page_text[:2000]}")

        await page.screenshot(path="dk_screenshot.png")
        print("Screenshot saved")

        await browser.close()

    with open("all_responses.json", "w", encoding="utf-8") as f:
        json.dump({}, f)

asyncio.run(capture())
