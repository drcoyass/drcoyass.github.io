import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="/Users/coyass/kaihatsu/drcoyass-site/notebooklm_auth.json")
        page = await context.new_page()
        
        await page.goto("https://notebooklm.google.com/notebook/5373977f-c317-4684-a2f5-58431e6e404c", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(10)
        
        print("--- Finding Add Source Buttons ---")
        elements = await page.query_selector_all('text="ソースを追加"')
        for el in elements:
            tag = await el.evaluate('el => el.tagName')
            role = await el.evaluate('el => el.getAttribute("role")')
            aria = await el.evaluate('el => el.getAttribute("aria-label")')
            disabled = await el.evaluate('el => el.disabled || el.getAttribute("aria-disabled")')
            print(f"Tag: {tag}, Role: {role}, Aria-label: {aria}, Disabled: {disabled}")
            
        print("--- Finding other buttons ---")
        buttons = await page.query_selector_all('button')
        for b in buttons:
            text = await b.inner_text()
            aria = await b.evaluate('el => el.getAttribute("aria-label")')
            if 'ソース' in text or (aria and 'ソース' in aria) or '追加' in text or (aria and '追加' in aria):
                disabled = await b.evaluate('el => el.disabled || el.getAttribute("aria-disabled")')
                print(f"Button Text: {text.strip()}, Aria-label: {aria}, Disabled: {disabled}")
        
        await browser.close()

asyncio.run(main())
