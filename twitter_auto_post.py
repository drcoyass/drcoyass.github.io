import asyncio
from playwright.async_api import async_playwright
import time
import os
import json
from pathlib import Path

# ==========================================
# 🚀 X (Twitter) 自動スレッド投稿スクリプト
# ==========================================
# 準備:
# 1. pip install playwright
# 2. playwright install chromium
# 3. 事前にログイン状態を保存する必要があります。
# ==========================================

# 認証情報を保存するファイル
AUTH_FILE = "twitter_auth.json"

async def login_and_save_state(page, context):
    """手動ログインを行い、セッション状態を保存する"""
    print("Xのログイン画面を開きます。手動でログインを完了させてください。")
    await page.goto("https://x.com/i/flow/login")
    
    # ログイン完了（ホーム画面のタイムラインが表示されるなど）まで待機
    print("ログインが完了するのを待機しています...(最大5分)")
    try:
        # Xのホーム画面などにある要素を待つ。タイムアウトを5分(300000ms)に延長。
        await page.wait_for_selector('[data-testid="primaryColumn"]', timeout=300000)
        print("✅ ログイン成功！セッション情報を保存します。")
        await context.storage_state(path=AUTH_FILE)
    except Exception as e:
        print(f"❌ ログインの待機中にタイムアウトしました。: {e}")

async def post_thread(page, tweets):
    """複数のツイートをスレッド形式で投稿する"""
    print("投稿画面を開きます...")
    # Xはバックグラウンド通信が多くnetworkidleがタイムアウトしやすいのでdomcontentloadedに変更し、timeoutを60秒に延長
    await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)

    try:
        # 初回の入力エリアを確実に見つける
        print("最初の入力エリアを探しています...")
        first_textarea = '[data-testid="tweetTextarea_0"]'
        await page.wait_for_selector(first_textarea, timeout=15000)

        for i, tweet_text in enumerate(tweets):
            print(f"📝 {i+1}個目のポストを入力中...")
            
            # 入力エリアのセレクタ（スレッドの深さによって変わるため、番号を指定）
            textarea_selector = f'[data-testid="tweetTextarea_{i}"]'
            await page.wait_for_selector(textarea_selector, timeout=10000)
            await page.click(textarea_selector)
            
            # 少しずつ入力する（Playwrightの速急すぎる入力を防ぐ）
            await page.type(textarea_selector, tweet_text, delay=20)
            await asyncio.sleep(1)

            # 最後のツイート以外は「＋（ポストを追加）」ボタンを押す
            if i < len(tweets) - 1:
                print("➕ スレッドを追加します...")
                add_btn = '[data-testid="addButton"]'
                await page.wait_for_selector(add_btn, timeout=5000)
                await page.click(add_btn)
                await asyncio.sleep(2) # 新しい入力エリアが出るまで待機

        # 「ポストする（すべてポスト）」ボタンを押す
        print("🚀 全てのポストを送信します！")
        # 複数スレッドの場合、tweetButtonInlineではなく単なるtweetButtonになるか、「すべてポスト」というテキストになる
        submit_btn_selectors = [
            'div[role="button"]:has-text("すべてポスト")',
            'div[role="button"]:has-text("ポストする")',
            'div[role="button"]:has-text("Post all")',
            '[data-testid="tweetButton"]',
            '[data-testid="tweetButtonInline"]'
        ]
        
        button_clicked = False
        for selector in submit_btn_selectors:
            btn = await page.query_selector(selector)
            if btn:
                is_disabled = await btn.get_attribute('aria-disabled')
                if is_disabled != "true":
                    print(f"✅ 有効な投稿ボタン ({selector}) を発見し、クリックします。")
                    await btn.click()
                    button_clicked = True
                    break
                    
        if not button_clicked:
            raise Exception("画面上に有効な「投稿（すべてポスト）」ボタンが見つかりませんでした。")
        
        # 送信完了を待機
        await asyncio.sleep(5)
        print("✅ スレッドの投稿が完了しました！")
        
    except Exception as e:
        print(f"⚠️ 投稿処理中にエラーが発生しました: {e}")
        print("現在の画面を 'error_x_post.png' として保存します。")
        await page.screenshot(path="error_x_post.png")
        raise e

async def main():
    DATA_DIR = Path("/Users/coyass/kaihatsu/drcoyass-site/集めた論文")
    DRAFT_FILE = DATA_DIR / "latest_thread_draft.txt"
    
    if not DRAFT_FILE.exists():
        print(f"⚠️ スレッド原案 ({DRAFT_FILE}) が見つかりません。先に notebooklm_auto_upload.py を実行してください。")
        return
        
    with open(DRAFT_FILE, "r", encoding="utf-8") as f:
        draft_text = f.read()
        
    # ツイート本文を抽出するより確実な方法
    import re
    
    # "【Xツイート目】" で始まるブロックを探す
    tweet_blocks = re.split(r'【\d+ツイート目】\s*', draft_text)
    
    thread_content = []
    
    # 最初の要素は「〜スレッドを作成しました」などの前置きなのでスキップ
    for block in tweet_blocks[1:]:
        # ブロック内の不要なメタ情報を消す（keep_pin以降など）
        # 最初に出現する "keep_pin" や "各ツイートはそのまま" などの前までを採用
        clean_text = block.split("各ツイートはそのまま")[0].split("keep_pin")[0].split("----------------")[0]
        
        clean_text = clean_text.strip()
        
        if not clean_text:
            continue
            
        # NotebookLM特有の引用数字（文末の「12」や「13」など、1〜2桁の数字）を削除する
        # パターン：文字のすぐ後ろにある数字（例：「力を発揮します1」「防ぎます13。」など）
        # 文末（。の手前）や行末にあることが多い
        clean_text = re.sub(r'([^\d\s])\d{1,2}(?=[。、\n\r]|$)', r'\1', clean_text)
        
        # ツイートの長さにふさわしい行であれば追加
        if len(clean_text) > 5:
            thread_content.append(clean_text)

    if not thread_content:
        print("⚠️ 投稿する内容が抽出できませんでした。原稿ファイルを確認してください。")
        return
        
    # ==========================================
    # 🛡️ 投稿前 自動バリデーション（安全装置）
    # ==========================================
    print("🔍 投稿前の安全チェックを実行しています...")
    
    # 1. 投稿数の異常チェック（1件だけ、または多すぎる場合はAIのパース失敗の可能性）
    if len(thread_content) < 2 or len(thread_content) > 10:
        print(f"🚨 【エラー】ツイートの数が異常です（{len(thread_content)}件）。原稿が正しく生成されていない可能性があるため処理を中止します。")
        return
        
    # NGワードリスト（これらが含まれていたらUIのゴミが入っている判定）
    ng_words = ["keep_pin", "メモに保存", "copy_all", "フラッシュ カード", "インフォグラフィック", "個のソース", "音声解説", "動画解説"]
    
    for i, tweet in enumerate(thread_content):
        # 2. 文字数チェック（Xの全角140文字制限）
        # ※URL等の半角英数は0.5文字扱いですが、ここでは厳密に単純な全角140文字としてチェックします
        if len(tweet) > 140:
            print(f"🚨 【エラー】{i+1}個目のツイートが140文字を超えています（{len(tweet)}文字）。構成がおかしい可能性があるため処理を中止します。")
            return
            
        # 3. ゴミテキスト混入チェック
        for ng in ng_words:
            if ng in tweet:
                print(f"🚨 【エラー】ツイート内に不要なUIテキスト（{ng}）が検出されました。処理を中止します。")
                return
                
        # 4. 出典番号の除去漏れチェック（文末の1〜2桁の数字）
        # 正規表現の除去機能が漏らしたケースの最終防壁
        if re.search(r'[^\d\s]\d{1,2}$', tweet) or re.search(r'[^\d\s]\d{1,2}。$', tweet):
            print(f"🚨 【エラー】ツイートの文末にNotebookLMの出典番号と思われる不自然な数字が残っています。手動で原稿を修正してください。\n（該当: {tweet[-10:]}）")
            return
            
    print("✅ 安全チェック通過。全てのツイートは正常なフォーマットです！\n")
    # ==========================================
        
    print(f"📄 {len(thread_content)}件のツイートからなるスレッドを投稿します。")

    async with async_playwright() as p:
        # ブラウザ起動時のBot検知回避オプション
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars'
        ]
        
        # 認証ファイルが存在するかチェック
        if os.path.exists(AUTH_FILE):
            print("🔑 保存されたセッションを使ってブラウザを起動します。")
            # ブラウザ画面を出さずに裏で実行するため headless=True に変更
            browser = await p.chromium.launch(headless=True, channel="chrome", args=browser_args)
            context = await browser.new_context(storage_state=AUTH_FILE)
            page = await context.new_page()
            
            try:
                await post_thread(page, thread_content)
            except Exception as e:
                print(f"⚠️ 投稿中にエラーが発生しました: {e}")
                print("\n=======================================================")
                print("🚨 X (Twitter) のログインセッションが期限切れの可能性があります。")
                print("以下のコマンドを実行して、古くなった認証ファイルを削除し、再度ログインしてください。")
                print("1. rm twitter_auth.json")
                print("2. python3 twitter_auto_post.py")
                print("=======================================================\n")
            
            await browser.close()
        else:
            print("⚠️ 認証情報がありません。初回ログインを行います。")
            browser = await p.chromium.launch(headless=False, channel="chrome", args=browser_args)
            context = await browser.new_context()
            page = await context.new_page()
            
            await login_and_save_state(page, context)
            await browser.close()
            print("💡 次回実行時から、自動でスレッドが投稿されるようになります。")

if __name__ == "__main__":
    asyncio.run(main())
