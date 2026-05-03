import asyncio
from playwright.async_api import async_playwright
import os

# ==========================================
# 🔑 Facebook 手動ログイン＆セッション保存スクリプト
# ==========================================
# 目的: Facebookに手動でログインし、その認証状態（Cookie等）を
#      'facebook_auth.json' に保存します。
#      次回以降、このファイルを使って自動投稿を行います。
# ==========================================

AUTH_FILE = "facebook_auth.json"

async def main():
    print("🚀 ブラウザを起動します...")
    
    browser_args = [
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars'
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=browser_args)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔵 Facebookのログイン画面にアクセスしています...")
        await page.goto("https://www.facebook.com/")

        print("\n=========================================================")
        print("💡 ブラウザ上でFacebookに【手動で】ログインしてください。")
        print("   ※二段階認証などがある場合はそれも完了させてください。")
        print("   ※ホーム画面（ニュースフィード）が表示されるまで進めてください。")
        print("=========================================================\n")

        print("⏳ ログインの完了を待機しています（最大5分）...")
        try:
            # ログイン成功の指標: ホーム画面の特定の要素（例：投稿作成ボタン等のrole="button"やaria-label）
            # Facebookは頻繁にDOMが変わりますが、「何らかのメニュー」「ナビゲーション」があることで判定
            await page.wait_for_selector('div[role="navigation"]', timeout=300000)
            # 安全のため少し待機してから保存
            await asyncio.sleep(5)
            
            print("✅ ログインが完了したようです！")
            print(f"💾 セッション情報を '{AUTH_FILE}' に保存しています...")
            await context.storage_state(path=AUTH_FILE)
            print("🎉 保存が完了しました！これで自動投稿の準備は完了です。")

        except Exception as e:
            print(f"❌ 待機中にタイムアウトしたか、エラーが発生しました: {e}")
            print("もう一度スクリプトを実行し直してください。")
        
        finally:
            print("ブラウザを閉じます。")
            await context.close()

if __name__ == "__main__":
    asyncio.run(main())
