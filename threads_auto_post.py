import asyncio
from playwright.async_api import async_playwright
import os
import time

# ==========================================
# 🚀 Threads 自動投稿スクリプト
# ==========================================

from pathlib import Path
STATE_FILE = "threads_auth.json" # Manual script created threads_auth.json
DATA_DIR = Path("/Users/coyass/kaihatsu/drcoyass-site/集めた論文")
DRAFT_FILE = DATA_DIR / "latest_thread_draft.txt"

async def post_to_threads(page, tweets):
    print("Threadsのホーム画面を開いています...")
    await page.goto("https://www.threads.net/")
    
    # 完全に読み込まれるまで待機
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(5)
    
    page_title = await page.title()
    print(f"現在のページタイトル: {page_title}")

    # ログイン状態の確認（ログインボタン等があれば失敗している）
    login_btn = await page.query_selector('div[role="button"]:has-text("ログイン"), div[role="button"]:has-text("Log in")')
    if login_btn:
        print("⚠️ 画面上に「ログイン」ボタンが見つかりました。セッション保存がうまく機能していないか、期限切れの可能性があります。")

    print("投稿エリアを探しています...")
    try:
        # ThreadsのデスクトップUIでは「スレッドを開始...」というプレースホルダーや、上部の作成アイコンをクリックする必要がある場合がある
        # まずは直接 contenteditable を探す
        input_selector = '[contenteditable="true"]'
        
        # もし見つからなければ、「スレッドを開始」や「Start a thread」などのテキストをクリックしてモーダルを開く
        start_thread_area = await page.query_selector('text="スレッドを開始"') or await page.query_selector('text="Start a thread"')
        if start_thread_area:
            print("「スレッドを開始」ボタンをクリックします...")
            await start_thread_area.click()
            await asyncio.sleep(2)
        else:
            # 鉛筆アイコン（作成ボタン）を探してクリック
            write_icon = await page.query_selector('svg[aria-label="作成"]') or await page.query_selector('svg[aria-label="Write"]')
            if write_icon:
                print("「作成」アイコンをクリックします...")
                await write_icon.click()
                await asyncio.sleep(2)

        # 改めてテキストボックスを探す（Playwright専用の :visible セレクタを利用して画面に表示されている要素のみ特定）
        # 最初の投稿のテキストボックス
        input_selector = '[contenteditable="true"]:visible'
        await page.wait_for_selector(input_selector, timeout=10000)
        
        # ツイート（スレッド要素）を一つずつ投稿ボックスに追加していく
        for i, tweet_text in enumerate(tweets):
            print(f"📝 {i+1}個目のスレッドを入力中...")
            
            # アクティブなテキストボックス（最後に追加されたもの）を探す
            textareas = await page.query_selector_all(input_selector)
            current_textarea = textareas[-1]
            
            await current_textarea.click()
            await asyncio.sleep(0.5)
            
            # テキストを入力
            await current_textarea.type(tweet_text, delay=20)
            await asyncio.sleep(1)
            
            # 最後以外のツイートの場合は「追加」ボタンを押して新しい入力枠を出す
            if i < len(tweets) - 1:
                # Threadsでのスレッド追加は通常Enterの連続や特定の「+」ボタンだが、
                # Playwrightからは改行を2回送るか、「スレッドに追加」ボタンを探す。
                add_thread_btn = await page.query_selector('svg[aria-label="スレッドに追加"]') or await page.query_selector('svg[aria-label="Add to thread"]')
                if add_thread_btn:
                    await add_thread_btn.click()
                else:
                    # 見つからなければEnterで改行し続けてみる(Threadsの仕様による)
                    await current_textarea.press("Enter")
                    await current_textarea.press("Enter")
                    await current_textarea.press("Enter")
                await asyncio.sleep(1)
        
        # [投稿]ボタンを探してクリック
        print("投稿ボタンをクリックしています...")
        await asyncio.sleep(2)
        
        # 日本語「投稿」、英語「Post」の両方に対応
        post_button_selector = 'div[role="button"]:has-text("投稿"), div[role="button"]:has-text("Post")'
        buttons = await page.query_selector_all(post_button_selector)
        # 通常、複数見つかる場合は一番最後（または有効なもの）がダイアログ上の投稿ボタン
        for btn in reversed(buttons):
            is_disabled = await btn.get_attribute('aria-disabled')
            if is_disabled != "true":
                await btn.click()
                print("🚀 投稿コマンドを送信しました！")
                break
                
        # 投稿の完了（ダイアログが閉じるなど）を待つ
        await asyncio.sleep(5)
        print("✅ Threadsへの投稿が完了しました！")
        
    except Exception as e:
        print(f"⚠️ 投稿処理中にエラーが発生しました: {e}")
        # エラー時の画面状態をスクショで保存
        print("現在の画面のスクリーンショットを 'error_threads.png' として保存します。")
        await page.screenshot(path="error_threads.png")
        raise e


async def main():
    if not os.path.exists(DRAFT_FILE):
        print(f"⚠️ エラー: '{DRAFT_FILE}' が見つかりません。先に notebooklm_auto_upload.py を実行してください。")
        return

    print(f"📄 '{DRAFT_FILE}' から投稿内容を読み込んでいます...")
    with open(DRAFT_FILE, "r", encoding="utf-8") as f:
        draft_text = f.read()

    import re
    tweet_blocks = re.split(r'【\d+ツイート目】\s*', draft_text)
    tweets = []

    for block in tweet_blocks[1:]:
        clean_text = block.split("各ツイートはそのまま")[0].split("keep_pin")[0].split("----------------")[0]
        clean_text = clean_text.strip()
        if not clean_text:
            continue
            
        clean_text = re.sub(r'([^\d\s])\d{1,2}(?=[。、\n\r]|$)', r'\1', clean_text)
        
        ng_words = ["keep_pin", "メモに保存", "copy_all", "フラッシュ カード", "インフォグラフィック", "個のソース", "音声解説", "動画解説"]
        skip = False
        for ng in ng_words:
            if ng in clean_text:
                print(f"🚨 原稿内に不要なUIテキスト（{ng}）が検出されました。処理を中止します。")
                return
                
        if len(clean_text) > 5:
            tweets.append(clean_text)

    if not tweets:
        print("⚠️ 投稿する内容が空です。")
        return

    print(f"✅ {len(tweets)} 件のスレッドとして投稿を準備します。")

    async with async_playwright() as p:
        if not os.path.exists(STATE_FILE):
            print(f"⚠️ 認証ファイル '{STATE_FILE}' が見つかりません。")
            print("先に threads_login_manual.py を実行してログインを完了させてください。")
            return

        print("🔑 保存されたセッションを使ってブラウザを起動します。")
        # 本番環境ではheadless=Trueにしますが、動作確認のためFalse（画面表示あり）にしています
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=STATE_FILE)
        page = await context.new_page()
        
        try:
            await post_to_threads(page, tweets)
        except Exception as e:
            print(f"⚠️ 投稿中にエラーが発生しました: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
