import asyncio
from playwright.async_api import async_playwright
import os
import re
from pathlib import Path

# ==========================================
# 🚀 Facebook 自動投稿スクリプト
# ==========================================
# 目的: 生成された論文解説の内容（スレッド形式）を結合して
#      Facebookに一つの投稿として自動投稿します。
# 準備: 事前に facebook_login_manual.py を実行して
#      facebook_auth.json を作成しておくこと。
# ==========================================

STATE_FILE = "facebook_auth.json"
DATA_DIR = Path("/Users/coyass/kaihatsu/drcoyass-site/集めた論文")
DRAFT_FILE = DATA_DIR / "latest_thread_draft.txt"

async def post_to_facebook(page, post_content):
    print("🔵 Facebookの対象ページを開いています...")
    await page.goto("https://www.facebook.com/COYASS/", wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)
    
    # ログイン画面に戻されてないかチェック
    title = await page.title()
    if "ログイン" in title or "Log In" in title:
        print("⚠️ セッションが切れ、ログイン画面が表示されています。")
        raise Exception("Facebook Login Required")
        
    print("✍️ 投稿エリア（「投稿を作成」など）を探しています...")
    try:
        # Facebook ページの投稿作成ボタン（"投稿を作成"、"Create post" など）をクリック
        create_post_btn = await page.query_selector('div:has-text("投稿を作成"), div:has-text("ページで投稿する"), div:has-text("Create Post"), div[role="button"]:has(span)')
        fallback_clicked = False
        if create_post_btn:
            # 何個か見つかるので最新のUIに従ってクリック
            nodes = await page.query_selector_all('div[role="button"]')
            for node in nodes:
                text = await node.inner_text()
                if text and ("シェアしよう" in text or "mind" in text or "何してる" in text or "投稿を作成" in text or "ページで投稿する" in text or "Create Post" in text):
                    await node.click(force=True)
                    fallback_clicked = True
                    break
                    
        if not fallback_clicked:
            # 汎用的な方法：aria-label等で探すか、/の後に作成するショートカットキー(pキー)を叩くなど。一番確実なのは "What's on your mind?" 系。
            spans = await page.query_selector_all('span')
            for span in spans:
                text = await span.inner_text()
                if "シェアしよう" in text or "mind" in text or "投稿を作成" in text or "ページで投稿する" in text:
                    await span.click(force=True)
                    fallback_clicked = True
                    break
                    
        if not fallback_clicked:
            print("⚠️ 投稿作成ボタンが見つかりません。現在の画面を保存します。")
            await page.screenshot(path="error_facebook_nmp.png")
            raise Exception("Cannot find create post button")
            
        await asyncio.sleep(3)
        
        print("📝 モーダル内のテキストエリアに入力しています...")
        # モーダルダイアログ内の入力エリアを探す
        modal_input = await page.query_selector('div[role="dialog"] p, div[role="dialog"] div[data-text="true"], div[role="textbox"]')
        
        if modal_input:
            await modal_input.click()
            await asyncio.sleep(1)
            
            # クリップボード経由の方が改行が綺麗に保たれるが、OS環境依存なので直接JSかTypeで。
            safe_body = post_content.replace('`', '\\`')
            
            # evaluateでのディスパッチを試みる（Playwrightのtypeだと長文が遅い＆エラーになりやすいため）
            await page.evaluate(f'''() => {{
                const textEvent = new InputEvent('insertText', {{
                    data: `{safe_body}`,
                    inputType: 'insertText',
                    bubbles: true,
                    cancelable: true
                }});
                document.activeElement.dispatchEvent(textEvent);
            }}''')
            
            # evaluateでダメだったときのためにちょっと待って確認
            await asyncio.sleep(2)
            content_in_box = await page.evaluate('document.activeElement.innerText')
            if len(content_in_box) < 10:
                print("   （直接のinsertTextに失敗。typeコマンドにフォールバックします...）")
                # fallback: 普通に打ち込む
                await page.keyboard.type(post_content, delay=5)
                
            await asyncio.sleep(3)
            
            # 「投稿」ボタンをクリックする
            print("🚀 投稿コマンドを送信します...")
            post_btns = await page.query_selector_all('div[role="dialog"] div[role="button"]')
            for btn in post_btns:
                btn_text = await btn.inner_text()
                if btn_text and ("投稿" in btn_text or "Post" in btn_text):
                    is_disabled = await btn.get_attribute('aria-disabled')
                    if is_disabled != "true":
                        await btn.click()
                        break
            
            # コマンド送信後、モーダルが消えるまで待機
            await asyncio.sleep(10)
            print("✅ Facebookへの投稿が完了したはずです！")
            
        else:
            raise Exception("Cannot find modal textbox")
            
    except Exception as e:
        print(f"⚠️ 投稿処理中にエラーが発生しました: {e}")
        await page.screenshot(path="error_facebook_post.png")
        raise e

async def main():
    if not os.path.exists(STATE_FILE):
        print(f"⚠️ エラー: '{STATE_FILE}' が見つかりません。先に facebook_login_manual.py を実行してください。")
        return

    if not DRAFT_FILE.exists():
        print(f"⚠️ 原稿 ({DRAFT_FILE}) が見つかりません。")
        return
        
    print(f"📄 '{DRAFT_FILE}' から投稿内容を読み込んでいます...")
    with open(DRAFT_FILE, "r", encoding="utf-8") as f:
        draft_text = f.read()
        
    # X用スレッドのように【Xツイート目】で区切られているものを結合する
    tweet_blocks = re.split(r'【\d+ツイート目】\s*', draft_text)
    paragraphs = []
    
    for block in tweet_blocks[1:]:
        clean_text = block.split("各ツイートはそのまま")[0].split("keep_pin")[0].split("----------------")[0]
        clean_text = clean_text.strip()
        if not clean_text:
            continue
            
        # UI残骸などの除去
        clean_text = re.sub(r'([^\d\s])\d{1,2}(?=[。、\n\r]|$)', r'\1', clean_text)
        
        # NGワードが含まれている場合はスキップや警告
        ng_words = ["keep_pin", "メモに保存", "copy_all", "フラッシュ カード", "インフォグラフィック", "個のソース", "音声解説", "動画解説"]
        for ng in ng_words:
            if ng in clean_text:
                 print(f"🚨 原稿内に不要なUIテキスト（{ng}）が検出されました。処理を中止します。")
                 return
                 
        if len(clean_text) > 5:
            paragraphs.append(clean_text)

    if not paragraphs:
        print("⚠️ 投稿する内容が抽出できませんでした。")
        return

    # Facebookの場合はスレッド制ではないので全てまとめて改行で繋ぐ
    # 見栄えを良くするため、間に装飾線などを入れるのも一案
    # (今回はシンプルに空行で区切って繋ぐ)
    post_content = "\n\n".join(paragraphs)
    
    print("✅ 安全チェック通過。Facebookへの投稿を開始します...")

    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-notifications'
        ]
        
        # 本番ではheadlessにしてもよいが、ログイン維持などの確認のため一旦FalseかTrueにするか。
        # 安定重視で headless=True を使用。
        browser = await p.chromium.launch(headless=True, args=browser_args)
        context = await browser.new_context(storage_state=STATE_FILE)
        page = await context.new_page()
        
        try:
             await post_to_facebook(page, post_content)
        except Exception as e:
             print(f"⚠️ エラー: {e}")
             print("セッションが切れている可能性があるため、facebook_login_manual.py を再実行してください。")
             
        finally:
             await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
