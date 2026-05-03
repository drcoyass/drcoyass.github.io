import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

# --- 設定エリア ---
# 操作対象のNotebookLM URL（ユーザー様指定の特定のNotebook）
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/5373977f-c317-4684-a2f5-58431e6e404c"
# 認証情報を保存するファイル名（Xの時と同じディレクトリ階層に置く）
AUTH_FILE = "notebooklm_auth.json"
# 論文データが保存されているディレクトリ
DATA_DIR = Path("/Users/coyass/kaihatsu/drcoyass-site/集めた論文")
# 最新の取得結果（追加すべきターゲット）のJSONファイル
TARGET_DATA_FILE = DATA_DIR / "latest_targets.json"

async def login_and_save_state(page, context):
    """手動ログイン（Googleアカウント）を行い、セッション状態を保存する"""
    print("NotebookLMの画面を開きます。Googleアカウントでログインを完了させてください。")
    print("※ ログイン後、指定のNotebookの画面が開くまでお待ちください。")
    await page.goto(NOTEBOOK_URL)
    
    # ノートブックの画面読み込み（ソース追加ボタン等が表示されるまで）を待機
    print("ログインが完了し、Notebookの画面が表示されるのを待機しています...(最大5分)")
    try:
        # NotebookLMの画面特有の要素（ソース追加ボタン、チャットボックスなど）が現れるまで待つ
        await page.wait_for_selector('textarea, button[aria-label="Add source"], div[role="button"]:has-text("ソース")', timeout=300000)
        print("✅ ログイン成功！セッション情報を保存します。")
        await context.storage_state(path=AUTH_FILE)
    except Exception as e:
        print(f"❌ ログインの待機中にタイムアウトしました: {e}")

async def upload_sources_to_notebook(page, targets):
    """対象のPDFやURLをNotebookLMのソースとして追加する"""
    print("\n🚀 NotebookLMの画面を開きます...")
    await page.goto(NOTEBOOK_URL, wait_until="domcontentloaded", timeout=60000)
    # UIの完全なレンダリングを長めに待機
    await asyncio.sleep(15)
    
    # 処理開始直前に、現在の画面状態をデバッグ用として保存
    debug_img1 = DATA_DIR / "debug_notebooklm_start.png"
    await page.screenshot(path=str(debug_img1))
    print(f"📸 現在の画面状態を保存しました: {debug_img1}")
    
    for i, target in enumerate(targets):
        title = target.get("title", "")
        pmid = target.get("pmid", "")
        data_type = target.get("type", "")
        path_or_url = target.get("path_or_url", "")
        
        print(f"\n📂 [{i+1}/{len(targets)}] ソースを追加中: {title[:30]}...")
        
        try:
            # 「ソースを追加」ボタン（＋ボタンや "Add source" などのテキストを持つボタン）を探す
            add_btn_selectors = [
                'span.mdc-button__label:has-text("ソースを追加")',
                'span.mdc-button__label:has-text("Add source")',
                'button:has(span.mdc-button__label:has-text("ソースを追加"))',
                'button[aria-label*="source"]',
                'button[aria-label*="ソース"]',
                'button[aria-label*="追加"]',
                'div[role="button"]:has-text("Add source")',
                'div[role="button"]:has-text("ソースを追加")',
                'div[role="button"]:has-text("追加")',
                'button:has-text("ソース")',
                'button:has-text("Source")'
            ]
            
            clicked = False
            for selector in add_btn_selectors:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    clicked = True
                    break
                    
            if not clicked:
                print("⚠️ 「ソースを追加」ボタンが見つかりませんでした。UIが変わっている可能性があります。")
                await page.screenshot(path=str(DATA_DIR / f"debug_notebooklm_error_source_{i+1}.png"))
                continue
                
            await asyncio.sleep(3)
            
            if data_type == "pdf_file":
                # PDFファイルアップロードの場合
                print(f"   ⬆️ PDFファイルをアップロード: {Path(path_or_url).name}")
                
                async with page.expect_file_chooser(timeout=15000) as fc_info:
                    # NotebookLMの新しいUI上の「ファイルをアップロード」ボタン
                    file_btn_selectors = [
                        'text="ファイルをアップロード"',
                        'div:has-text("ファイルをアップロード")',
                        'span:has-text("ファイルをアップロード")',
                        'div[role="button"]:has-text("ファイルをアップロード")',
                        'input[type="file"]'
                    ]
                    
                    clicked_file = False
                    for f_selector in file_btn_selectors:
                        file_btn = await page.query_selector(f_selector)
                        if file_btn:
                            # If it's the hidden input, we don't click it directly
                            if "input" not in f_selector:
                                await file_btn.click()
                                clicked_file = True
                                break
                                
                    if not clicked_file:
                        # Try to find input directly if button click failed
                        input_file = await page.query_selector('input[type="file"]')
                        if input_file:
                            await input_file.set_files(path_or_url)
                            continue
                        else:
                            print("⚠️ ファイルアップロードボタンが見つかりません。")
                            await page.screenshot(path=str(DATA_DIR / f"debug_notebooklm_error_filebtn_{i+1}.png"))
                            continue
                        
                file_chooser = await fc_info.value
                await file_chooser.set_files(path_or_url)
                
            elif data_type == "url":
                # URL追加の場合（新しいUIでは「ウェブで新しいソースを検索」というメインの入力欄に直接入れる）
                print(f"   🔗 リンク（URL）を追加: {path_or_url}")
                
                await asyncio.sleep(2)
                
                # 1. ダイアログのメインテキストボックスを探す
                main_input_selectors = [
                    'input[placeholder*="ウェブで新しいソースを検索"]',
                    'textarea[placeholder*="ウェブで新しいソースを検索"]',
                    'dialog input[type="text"]',
                    '[role="dialog"] input[type="text"]',
                    '.mdc-text-field__input'
                ]
                
                input_found = False
                for sel in main_input_selectors:
                    inputs = await page.query_selector_all(sel)
                    for inp in inputs:
                        if await inp.is_visible():
                            await inp.fill(path_or_url)
                            input_found = True
                            break
                    if input_found:
                        break
                        
                if not input_found:
                    # 見つからなかった場合はとりあえず画面中央付近にキー入力
                    print("   （メイン入力欄が見つからないため、直接キーボード入力で試行します）")
                    await page.keyboard.type(path_or_url)
                    
                await asyncio.sleep(1)
                
                # 右側の矢印ボタン（次へ・追加）を探す。またはエンターキー
                arrow_btns = await page.query_selector_all('button[aria-label*="Next"] , button[aria-label*="次へ"] , button[aria-label*="検索"] , button[aria-label*="追加"]')
                clicked_arrow = False
                for btn in arrow_btns:
                    if await btn.is_visible() and await btn.is_enabled():
                        try:
                            await btn.click()
                            clicked_arrow = True
                            break
                        except:
                            pass
                            
                if not clicked_arrow:
                    await page.keyboard.press("Enter")
                    
                print("   （URL挿入操作完了）")
            
            # アップロード/追加が完了し、処理が終わるのを待機
            print("   ⏳ 処理完了を待機中...")
            await asyncio.sleep(15) 
            
            # もし「ソースを追加」ダイアログがまだ開いていれば閉じる（後ろのチャット欄を押すため）
            print("   （ダイアログを閉じています...）")
            close_btns = await page.query_selector_all('button[aria-label="Close dialog"], button[aria-label*="閉じる"], button[mat-dialog-close]')
            for btn in close_btns:
                if await btn.is_visible() and await btn.is_enabled():
                    try:
                        await btn.click()
                    except:
                        pass
            await asyncio.sleep(1)
            # 念のためEscapeキーも押す
            await page.keyboard.press("Escape")
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ❌ ソース追加中にエラー: {e}")
            await page.screenshot(path=str(DATA_DIR / f"debug_notebooklm_exception_{i+1}.png"))

async def send_prompt_and_save(page):
    """論文が追加された状態でプロンプトを送信し、結果を保存する"""
    print("\n💬 論文の要約・Xスレッド作成プロンプトを送信します...")
    
    prompt_text = """
新たにアップロードされた最新の歯科論文（ポリリン酸・ホワイトニング等）の内容を読み取り、以下の条件でSNS（X, Threads, Facebook）用の解説スレッド原稿を作成してください。

インプレッションを増やすための「動線」として、最後のツイートには必ず「さらに詳しい解説はnoteやFacebookでも公開中！プロフィールのリンクからチェックしてください！✨」といった誘導メッセージと、検索されやすい関連ハッシュタグ（#歯科医師 #ホワイトニング #論文解説 など）を適量入れてください。

【条件】
1. 専門用語を避け、一般の患者さんが興味を持てる「最新の知見」として驚きを与える構成にすること。
2. 5リプライ前後のスレッド形式にすること（各ツイートは140字以内の文章量目安）。
3. 各ツイートの先頭には必ず「【1ツイート目】」「【2ツイート目】」のように見出しをつけて、システムが文字を自動抽出できるようにすること。
4. トーン＆マナーは「最先端を追求するプロフェッショナルな歯科医師」を意識すること。
    """
    
    try:
        # 画面上のすべてのtextareaを取得し、一番最後にあり、かつモーダルダイアログ内にないものを探す
        # より確実にするため、プレースホルダーなどでチャットボックスを特定する
        chat_box = await page.query_selector('textarea[placeholder*="入力を開始します"], textarea[placeholder*="Ask"], textarea[aria-label*="Chat"], textarea[aria-label*="チャット"]')
        if not chat_box:
            # Fallback
            textareas = await page.query_selector_all('textarea')
            if textareas:
                chat_box = textareas[-1]
                
        if chat_box:
            await chat_box.fill(prompt_text)
            await asyncio.sleep(2)
            
            # 送信アクション
            sent = False
            
            # 1. 確実のため、少し長めに待ってから送信ボタンをクリック
            await asyncio.sleep(1)
            send_btns = await page.query_selector_all('button[aria-label*="Send"], button[aria-label*="送信"], button[aria-label*="提出"], button:has(mat-icon:has-text("send"))')
            for btn in send_btns:
                if await btn.is_visible() and not await btn.is_disabled():
                    try:
                        # 確実にクリックイベントを発火させる
                        await btn.evaluate("el => el.click()")
                        sent = True
                        break
                    except:
                        pass
                        
            # 2. ボタンクリックがダメならキーボードでEnter
            if not sent:
                await chat_box.focus()
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.5)
                # NotebookLMはCMD+EnterやCtrl+Enterで送信されるケースもある
                await page.keyboard.press("Control+Enter")
                await asyncio.sleep(0.5)
                await page.keyboard.press("Meta+Enter")
                
            print("   ⏳ AIの回答生成を待っています...(約40秒)")
            await asyncio.sleep(45) 
            
            # 回答テキストの抽出
            # 新しいUIではタグ構造が変わるため、画面の全テキストから直接切り出す作戦
            body_text = await page.evaluate("document.body.innerText")
            prompt_end_phrase = "歯科医師」を意識すること。"
            
            latest_response = ""
            if prompt_end_phrase in body_text:
                # 自分が送信したプロンプトの最後の一文を境目にして、その後ろ（＝AIの回答全文）を取得
                raw_response = body_text.split(prompt_end_phrase)[-1]
                # 全文そのままだと画面下部のボタンや注意事項まで入ってしまうため、不要な文字より前を切り取る
                clean_response = raw_response.split("入力を開始します")[0]
                clean_response = clean_response.split("NotebookLM は不正確な")[0]
                latest_response = clean_response.strip()
                
            # もし上記で取れなかった場合の緊急フォールバック
            if not latest_response or len(latest_response) < 50:
                 paragraphs = await page.query_selector_all('p, div[dir="auto"]')
                 for p in paragraphs:
                     text = await p.inner_text()
                     if len(text) > 100 and "【条件】" not in text and "歯科医師」を意識すること" not in text:
                         latest_response += text + "\n\n"

            if latest_response:
                # 保存
                out_path = DATA_DIR / "latest_thread_draft.txt"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(latest_response.strip())
                print(f"✅ スレッド原案を保存しました: {out_path}")
            else:
                print("⚠️ 回答テキストを抽出できませんでした。")
        else:
            print("⚠️ チャットボックスが見つかりません。")
            
    except Exception as e:
        print(f"❌ プロンプト送信・回答取得エラー: {e}")
        await page.screenshot(path=str(DATA_DIR / "debug_notebooklm_prompt_error.png"))

async def main():
    if not TARGET_DATA_FILE.exists():
        print("💡 最新のターゲット論文データ (latest_targets.json) が存在しません。先に pubmed_fetcher.py を実行してください。")
        return
        
    with open(TARGET_DATA_FILE, "r", encoding="utf-8") as f:
        targets = json.load(f)
        
    if not targets:
        print("💡 追加すべき新しい論文がありません。")
        return
        
    print(f"📦 {len(targets)} 件の論文ソースをNotebookLMへ追加します。")
    
    # ユーザー側のターミナル用にTMPDIRなどの設定は排除し、標準で起動
    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars'
        ]
        
        if os.path.exists(AUTH_FILE):
            print("🔑 保存されたセッションを使ってブラウザを起動します。(ウィンドウ表示)")
            browser = await p.chromium.launch(headless=False, channel="chrome", args=browser_args)
            context = await browser.new_context(storage_state=AUTH_FILE)
            page = await context.new_page()
            
            await upload_sources_to_notebook(page, targets)
            # 要約プロンプト送信
            await send_prompt_and_save(page)
            
            print("💡 全ての処理が完了しました。")
            await browser.close()
        else:
            print("⚠️ 認証情報がありません。初回Googleログインを行います。")
            # 初回は画面を出して手動ログインしてもらう
            browser = await p.chromium.launch(headless=False, channel="chrome", args=browser_args)
            context = await browser.new_context()
            page = await context.new_page()
            
            await login_and_save_state(page, context)
            
            # そのまま引き続き、初回からソースのアップロードとプロンプト送信を行う
            await upload_sources_to_notebook(page, targets)
            await send_prompt_and_save(page)
            
            print("💡 初回ログインとセッション保管、ソースの自動追加が完了しました！")
            await browser.close()
            print("処理を終了しました。")

if __name__ == "__main__":
    asyncio.run(main())
