import asyncio
from playwright.async_api import async_playwright
import os
import json
from pathlib import Path
import re

# ==========================================
# 📝 Note 自動下書き投稿スクリプト
# ==========================================
# 事前に note_login_manual.py を実行して note_auth.json を作成しておく必要があります。

AUTH_FILE = "note_auth.json"
DATA_DIR = Path("/Users/coyass/kaihatsu/drcoyass-site/集めた論文")
DRAFT_FILE = DATA_DIR / "latest_thread_draft.txt"

async def post_to_note(page, title, body):
    """Noteのエディタを開き、タイトルと本文を入力して下書き保存する"""
    print("📝 Noteの投稿（エディタ）画面を開きます...")
    await page.goto("https://note.com/intent/post", wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)
    
    current_url = page.url
    page_title = await page.title()
    print(f"現在のURL: {current_url}")
    print(f"現在のタイトル: {page_title}")
    if "ログイン" in page_title or "Log In" in page_title:
        print("⚠️ ログイン画面にリダイレクトされました。セッションが有効ではありません。")
        raise Exception("Note Login Required")
        
    try:
        # 1. タイトルの入力
        print("✍️ タイトルを入力しています...")
        # Noteのエディタのタイトル領域は divの他、textareaの場合がある
        # 新エディタや環境によってセレクタが変わるため複数指定
        title_selector = 'div[data-name="title"], textarea[placeholder*="タイトル"], .editor-title, .title-input'
        await page.wait_for_selector(title_selector, timeout=15000)
        await page.click(title_selector, force=True)
        await page.keyboard.type(title)
        await asyncio.sleep(1)
        
        # 2. 本文の入力
        print("✍️ 本文を入力しています...")
        # 本文領域をクリック
        body_selector = 'div[data-name="body"], .editor-content, [data-slate-editor="true"], .body-input'
        await page.wait_for_selector(body_selector, timeout=15000)
        await page.click(body_selector, force=True)
        
        # Playwrightの .type は長文だと遅いので、クリップボード経由か JS の insertText コマンドが安全
        # 今回は確実性を取るため、要素フォーカス後にペーストを模倣する手段で入力する
        # （単純に keyboard.type だと Note側のリッチエディタ挙動でおかしくなることがあるため）
        
        # JS用文字列エスケープ
        safe_body = body.replace('`', '\\`')
        
        await page.evaluate(f'''() => {{
            const textEvent = new InputEvent('insertText', {{
                data: `{safe_body}`,
                inputType: 'insertText',
                bubbles: true,
                cancelable: true
            }});
            document.activeElement.dispatchEvent(textEvent);
        }}''')
        # もし上記で入らなければフォールバック
        await asyncio.sleep(2)
        body_text_in_dom = await page.evaluate("document.activeElement.innerText")
        if len(body_text_in_dom) < 10:
             print("   （クリップボード方式にフォールバックします...）")
             await page.fill(body_selector, body) # fillも試す
             # 最終手段として1文字ずつ（少し時間がかかるが確実）
             if len(await page.evaluate("document.activeElement.innerText")) < 10:
                 await page.keyboard.type(body, delay=5)
                 
        await asyncio.sleep(3)
        
        # 3. 保存ボタンを押すか待つ
        # Noteは基本的に自動保存されるため、数秒待てば「保存しました」ステータスになる。
        # 必要なら「下書き保存」などの明示的な離脱を行う
        print("💾 自動保存を待機しています...")
        await asyncio.sleep(5)
        
        print("🎉 Noteへの下書き作成が完了しました！")
        
    except Exception as e:
        print(f"⚠️ Note投稿処理中にエラーが発生しました: {e}")
        await page.screenshot(path="error_note_post.png")
        raise e

async def main():
    if not DRAFT_FILE.exists():
        print(f"⚠️ 生成された原稿 ({DRAFT_FILE}) が見つかりません。")
        return
        
    with open(DRAFT_FILE, "r", encoding="utf-8") as f:
        draft_text = f.read()
        
    if not draft_text.strip():
        print("⚠️ 原稿の中身が空です。")
        return
        
    # ==========================================
    # 🧹 ゴミテキストの除去とバリデーション
    # ==========================================
    # Xのスクリプトと同じロジックで本文をクリーンアップする
    tweet_blocks = re.split(r'【\d+ツイート目】\s*', draft_text)
    clean_paragraphs = []
    
    for block in tweet_blocks[1:]:
        clean_text = block.split("各ツイートはそのまま")[0].split("keep_pin")[0].split("----------------")[0]
        clean_text = clean_text.strip()
        if not clean_text:
            continue
            
        clean_text = re.sub(r'([^\d\s])\d{1,2}(?=[。、\n\r]|$)', r'\1', clean_text)
        
        # NGワードチェック
        ng_words = ["keep_pin", "メモに保存", "copy_all", "フラッシュ カード", "インフォグラフィック", "個のソース", "音声解説", "動画解説"]
        for ng in ng_words:
            if ng in clean_text:
                print(f"🚨 【エラー】原稿内に不要なUIテキスト（{ng}）が検出されました。処理を中止します。")
                return
                
        if len(clean_text) > 5:
            clean_paragraphs.append(clean_text)

    if not clean_paragraphs:
        print("⚠️ 投稿する内容が抽出できませんでした。原稿ファイルを確認してください。")
        return
        
    # タイトルの生成（最初の段落の一部を使う）
    # 例：【最新論文解説】などを除去してクリーンなタイトルに
    first_p = clean_paragraphs[0]
    title = "[論文解説] " + first_p[:30] + ("..." if len(first_p) > 30 else "")
    title = title.replace("【条件】", "").replace("【最新論文解説】", "").strip()
    
    # 本文（クリーンアップされた段落を繋ぎ合わせる）
    body = "\n\n".join(clean_paragraphs)
    
    print("✅ 安全チェック通過。Noteの下書きを作成します...")

    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars'
        ]
        
        if os.path.exists(AUTH_FILE):
            print("🔑 認証情報を使ってNoteの裏側（ヘッドレス）で投稿準備をします。")
            browser = await p.chromium.launch(headless=True, args=browser_args)
            context = await browser.new_context(storage_state=AUTH_FILE)
            page = await context.new_page()
            
            try:
                await post_to_note(page, title, body)
            except Exception as e:
                print(f"⚠️ エラー: {e}")
                print("セッションが切れている可能性があるため、note_login_manual.py を再実行してください。")
            
            await browser.close()
        else:
            print("⚠️ 認証情報 note_auth.json がありません。まずは note_login_manual.py を実行してログインを済ませてください。")

if __name__ == "__main__":
    asyncio.run(main())
