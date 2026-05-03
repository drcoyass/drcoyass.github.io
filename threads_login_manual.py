import asyncio
from playwright.async_api import async_playwright
import os

# ==========================================
# 🧵 Threads 手動ログイン＆認証情報保存スクリプト
# ==========================================
# 実行するとブラウザが開くので、自分のInstagram/Threadsアカウントにログインしてください。
# ログイン後、ターミナルでEnterを押すとセッションが保存されます。

AUTH_FILE = "threads_auth.json"

async def login_and_save_state(page, context):
    print("🌍 Threadsのログイン画面を開きます。ブラウザ上でログインを完了させてください。")
    await page.goto("https://www.threads.net/login")
    
    print("⏳ ログイン手続きが完全に終わりましたら、この黒い画面（ターミナル）で Enterキー を押してください。")
    print("   手動でログイン状態を保存します。")
    
    # ユーザーがターミナルでEnterを押すまで無限待機
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, input, "")
    
    try:
        print("✅ ログイン状態を保存しています...")
        await context.storage_state(path=AUTH_FILE)
        print(f"🎉 認証情報を {AUTH_FILE} に保存しました！")
    except Exception as e:
        print(f"❌ 認証情報の保存に失敗しました: {e}")

async def main():
    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars'
        ]
        
        # 画面を表示して起動（手動操作のため）
        browser = await p.chromium.launch(headless=False, channel="chrome", args=browser_args)
        context = await browser.new_context()
        page = await context.new_page()
        
        await login_and_save_state(page, context)
        
        print("💡 設定完了です！ブラウザを閉じます。")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
