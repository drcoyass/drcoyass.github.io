import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        with open("threads_auth.json", "r") as f:
            state = json.load(f)
            await context.add_cookies(state.get("cookies", []))
            
        page = await context.new_page()
        await page.goto("https://www.threads.net/@dr.coyass/post/DU6yy-HlLD9", wait_until="networkidle")
        await asyncio.sleep(5)
        
        # 画面のボタンを出力
        btns = await page.evaluate('''() => {
            let results = [];
            let els = document.querySelectorAll('div[role="button"], button');
            for(let el of els) {
                results.push({
                    text: el.innerText,
                    textContent: el.textContent,
                    ariaLabel: el.getAttribute('aria-label') || "",
                    html: el.innerHTML.substring(0, 100)
                });
            }
            return results;
        }''')
        
        for i, b in enumerate(btns):
            print(f"[{i}] text='{b['text']}' textContent='{b['textContent']}' aria='{b['ariaLabel']}'")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
