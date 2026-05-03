import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chrome", args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context()
        page = await context.new_page()
        print("✅ Chrome launched successfully!")
        await page.goto("https://google.com")
        print("✅ Google loaded!")
        await browser.close()

asyncio.run(main())
