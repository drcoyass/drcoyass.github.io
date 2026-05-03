import asyncio
from playwright.async_api import async_playwright
import os
import json
import random
from pathlib import Path
import platform
import google.generativeai as genai

# 環境変数または .env ファイルからAPIキーを読み込む処理
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                GEMINI_API_KEY = line.strip().split("=")[1].strip('"\'')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("🤖 Gemini AI 連携が有効になりました。コメント文脈に合わせた返信を生成します。")
else:
    print("⚠️ GEMINI_API_KEY が設定されていません。ランダムな定型文で返信します。")

# ==========================================
# 🧵 Threads 指定投稿への自動返信（AIボット風）スクリプト
# ==========================================
# 前提: threads_login_manual.py でログインを済ませておくこと。

AUTH_FILE = "threads_auth.json"
TARGET_POST_URL = "https://www.threads.net/@dr.coyass/post/DU6yy-HlLD9"
REPLIED_USERS_FILE = "replied_threads_users.json"

def load_replied_users():
    if os.path.exists(REPLIED_USERS_FILE):
        with open(REPLIED_USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_replied_user(username):
    users = load_replied_users()
    users.add(username)
    with open(REPLIED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users), f)

# 今回はAPIキー不要ですぐ動くように、面白く返信するパターンをランダムに選びます。
# 170件以上のコメントに対応するため、バリエーションを増やします。
FUNNY_REPLIES = [
    "履歴書なのに美白モード！🤣 次はぜひ背景も宇宙にしましょう！✨",
    "証明写真機あるあるですね😂 盛れてれば全部オッケーです！👍",
    "いやいや、美肌は大事です！履歴書からオーラ出しちゃいましょう😎✨",
    "最近の証明写真機の「美肌モード」の威力ハンパないですよね😂 応援してます！",
    "一発勝負の証明写真、スリル満点ですね🤣 お疲れ様です！",
    "美白の恩恵は全力で受けていきましょう！✨",
    "証明写真ってなぜか緊張しますよね😂 綺麗に撮れて羨ましいです！",
    "美白モードの課金は実質無料みたいなもんです！👍",
    "むしろ履歴書こそ美白で勝負するべきです！🤣",
    "写真機のフラッシュが眩しすぎる問題😂 お疲れ様でした！",
    "次撮る時は「小顔モード」もフル稼働でいきましょう！😎",
    "美白モードで未来も明るく照らしていきましょう！✨",
    "証明写真あるある、納得いかないまま時間切れになるやつですね🤣",
    "美肌補正は現代の必須スキルです！👍 完璧です！",
    "履歴書の写真って何度撮っても慣れないですよね😂 ファイトです！"
]

def generate_ai_reply(username, comment_text, has_image=False):
    """Gemini AIを使って、コメントに自然に返信するテキストを生成する"""
    if not GEMINI_API_KEY:
        return random.choice(FUNNY_REPLIES)
        
    image_context = ""
    if has_image:
        image_context = """
【重要事項】
このユーザーは画像（おそらくAIで加工等をしたあなたの写真）を添付して返信しています！
文章の内容だけでなく、**「写真を加工してくれてありがとう！」「その写真いいですね！」「面白い写真ですね！」など、画像に対してリアクションする一言を必ず**含めてください。
"""

    prompt = f'''
あなたは「Dr. コヤス (Dr. Coyass)」という、親しみやすくユーモアのある現役歯科医師でありミュージシャンです。
現在、あなたがThreadsに投稿した「自分の非常勤講師用の証明写真（アフロヘアにサングラスという強烈なビジュアル）」に対して、ユーザーからコメントが来ています。

以下の「ユーザーのコメント内容」に対して、文脈に沿った面白い返信（リプライ）を考えてください。
ただし、以下のルールを厳守してください。

【ルール】
1. 最大でも2〜3文程度の短い返信にすること。
2. 絵文字（😂、✨、👍、🤣など）を自然に使うこと。
3. 相手のツッコミや感想にしっかり乗っかる、または上手く切り返すこと。
4. 出力は返信テキストのみ（「はい、生成しました」などの前置きは絶対に入れない）。
{image_context}

ユーザー名: {username}
ユーザーのコメント内容（ノイズが含まれる場合があります）:
{comment_text}
    '''
    
    try:
        # 利用可能なモデルのリストに従ってフェールオーバー
        model_names = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-2.5-pro'
        ]
        
        response = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    break # 成功したらループを抜ける
            except Exception:
                continue # エラーが起きたら次のモデルを試す
                
        if not response or not response.text:
             return "（AIからの返信生成に失敗しました🙏）"
             
        text = response.text.strip()
        if text:
            return text
        return random.choice(FUNNY_REPLIES)
    except Exception as e:
        print(f"⚠️ AI返信生成中にエラーが発生しました: {e}")
        return random.choice(FUNNY_REPLIES)

async def reply_to_comments(page):
    print(f"🌍 対象の投稿を開いています... ({TARGET_POST_URL})")
    await page.goto(TARGET_POST_URL, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)
    
    replied_count = 0
    replied_users_db = load_replied_users()
    idle_scrolls = 0
    max_idle_scrolls = 15 # 15回連続で新しいコメントがなければ終了（一番下まで到達したと判定）
    
    print("🚀 スクロールしながらコメントへの返信を開始します...")
    
    for scroll_step in range(300): # 無限ループ防止のため最大300回のスクロールに制限
        # Playwrightの標準機能だと画面外（かつて上の方にあった）ボタンも取得してしまい、上に逆戻りする原因になるため、
        # JavaScriptを使って「現在実際に画面に映っている（viewport内にある）」返信ボタンだけを抽出する
        btns_info = await page.evaluate('''() => {
            let results = [];
            let btns = document.querySelectorAll('div[role="button"], button');
            
            for (let btn of Array.from(btns)) {
                let html = btn.innerHTML || "";
                let text = btn.innerText || "";
                
                // 「トップ」や「アクティビティを見る」のような明確な文字ボタンは除外
                if (text && isNaN(parseInt(text.trim()))) {
                    continue;
                }
                
                // Threadsの返信(吹き出し)アイコンのSVGが含まれているか判定
                // 返信アイコンの代表的なタグやクラス、またはd="..."の一部で判定する（変更されやすいため複数パターンのどれか）
                let hasReplyIcon = html.includes('d="M12.004') || html.includes('d="M20.656') || html.includes('<svg') && !html.includes('d="M12 22a10') && !html.includes('d="M18.8 9.548') && !html.includes('d="M19.122');
                
                // いいね(M12 22a10等), リポスト(M19.122等), シェア(M18.8 9.5等) は除外した上でSVGを持つボタンを探す、
                // あるいは特定の包含構造を持つボタンに絞る。
                // より確実なのは "自身の次の要素がリポストボタンである" などの構造的判定。
                // ※ ここは簡易的に「svgを持ち、かつ文字が含まれないか数字のみ」を採用する。
                if (!html.includes('<svg')) continue;
                
                // ただし、いいねボタン等を除外するため、SVGのパス(d=)に吹き出し特有の文字列が含まれているかチェック
                // （一番確実なのは「返信」を示す viewBox="0 0 24 24" と特定の d="" です）
                // 吹き出しアイコンは通常 'M12.004', '20.656' などの座標を持ちますが、
                // とりあえず「svgを含み、テキストが数字か空の中の2番目のボタン（いいね、返信、リポストの順）」として扱うのは難しいので、
                // 要素の幅や高さ、親要素の構造から「アクションバーの中のボタン」を探します。
                
                // 今回は最もシンプルなヒューリスティック：
                // <svg>を持ち、かつ親がflex-row等で並んでいる4つのボタンの2つ目として特定するか、
                // 取得した要素のinnerHTMLに "M20.656"（吹き出しマークの典型パスの一部）を含むかで判定
                let isReplyBtn = html.includes('M20.656');
                
                // もしM20.656が含まれていれば確実。もし仕様変更で含まれていないなら、テキストが数字のみか空のボタンを採用
                if (!isReplyBtn && html.includes('<svg') && (!text || !isNaN(parseInt(text.trim())))) {
                     // いいね等の他ボタンも拾う可能性があるため厳密にはM20.656判定がベターだが、
                     // セーフティネットとして追加の検証をする（例：htmlに "M16.792 3.908" (Like) がないか等）
                     if(html.includes('M16.792') || html.includes('M12 22a10')) continue; // Like
                     if(html.includes('M19.998') || html.includes('M19.122')) continue; // Repost
                     if(html.includes('M21.235') || html.includes('M18.8 9.')) continue; // Share
                     
                     isReplyBtn = true;
                }
                
                if (!isReplyBtn) continue;
                
                if (btn.hasAttribute("data-bot-processed")) continue; // 処理済みマークがあるものは除外
                
                // 画面内に見えているかチェック
                let rect = btn.getBoundingClientRect();
                // ウィンドウの高さ内に収まっている要素だけを対象とする
                if (rect.top >= 0 && rect.bottom <= (window.innerHeight || document.documentElement.clientHeight)) {
                    let uniqueId = "reply_btn_" + Math.random().toString(36).substring(2);
                    btn.setAttribute("data-bot-id", uniqueId);
                    results.push(uniqueId);
                }
            }
            return {
                results: results
            };
        }''')
        
        btns_to_click = btns_info['results']
        found_new_reply_on_this_screen = False
        
        if btns_to_click:
            # 見えている未処理ボタンを順番に処理
            for btn_idx, btn_id in enumerate(btns_to_click):
                # Python側で該当のボタンを取得
                btn = await page.query_selector(f'[data-bot-id="{btn_id}"]')
                if not btn:
                    continue
                
                # 二度と取得しないように、処理済みマークをHTMLに確固たるものとして刻む
                try:
                    await btn.evaluate("node => node.setAttribute('data-bot-processed', 'true')")
                except:
                    pass
                
                # 最初のスクロール位置（一番上）での最初のボタンは親投稿自身の可能性があるため慎重に扱う
                if scroll_step == 0 and btn_idx == 0:
                    continue
                    
                try:
                    if await btn.is_visible() and await btn.is_enabled():
                        # クリック前に確実に見える位置まで少しスクロール
                        try:
                            await btn.scroll_into_view_if_needed()
                            # 上部のヘッダーに隠れないように少し上にスクロールバックする
                            await page.evaluate("window.scrollBy(0, -150)")
                            await asyncio.sleep(1)
                        except:
                            pass
                            
                        # クリック前に、ボタンの親要素（コメント枠全体）からテキスト情報と画像情報を取得する
                        # activeElementに頼ると画面上部の別の要素を誤認するため、ボタン自身を起点とする
                        extracted_data = await btn.evaluate('''btn => {
                            let current = btn;
                            let container = null;
                            for(let i=0; i<6; i++) {
                                if(current.parentElement) {
                                    current = current.parentElement;
                                    container = current;
                                }
                            }
                            
                            let text = container ? container.innerText : "";
                            let hasImage = container ? (container.querySelector('picture') !== null || container.querySelector('a[href*="/media"]') !== null) : false;
                            
                            return { text: text, hasImage: hasImage };
                        }''')
                        
                        raw_text = extracted_data['text'].strip() if extracted_data and extracted_data['text'] else ""
                        has_image = extracted_data['hasImage'] if extracted_data else False
                        
                        # Threadsの構造上、innerTextの1行目がユーザー名になる
                        username = raw_text.split('\\n')[0].strip() if raw_text else "unknown"
                        comment_text = raw_text
                        
                        if username == "dr.coyass" or username in replied_users_db:
                            print(f"⏩ {username} は対応済み（または自身）のためスキップします。")
                            continue
                            
                        print(f"👤 新規ユーザー発見: {username} への返信を準備中...")
                        found_new_reply_on_this_screen = True
                            
                        # 普通のclick()だと他の要素に遮られる事があるため、JSで強制クリック
                        await btn.evaluate("node => node.click()")
                        
                        # 入力エリアが出現するまで少し待つ
                        await asyncio.sleep(2)
                        
                        # Threadsは「返信」ボタンを押すと自動的に入力欄がフォーカスされる仕様のため、
                        # セレクタで探さずに直接キーボード入力を開始する
                        
                        print(f"👤 {username} のコメントを解析中... (画像あり: {has_image})")
                        chosen_reply = generate_ai_reply(username, comment_text, has_image)
                        print(f"✍️ 入力中...：「{chosen_reply}」")
                        
                        # 一旦キーボード入力で文字を流し込む
                        await page.keyboard.type(chosen_reply, delay=50)
                        await asyncio.sleep(1)
                        
                        # Reactに文字入力を認識させるためのダメ押し
                        await page.keyboard.press("Space")
                        await asyncio.sleep(0.5)
                        await page.keyboard.press("Backspace")
                        await asyncio.sleep(1)
                        
                        # 投稿ボタンを押す
                        post_btns = await page.query_selector_all('div[role="button"]:has-text("投稿")')
                        posted = False
                        for p_btn in post_btns:
                            # aria-disabled属性だけでなく、opacity等も確認する
                            is_disabled = await p_btn.get_attribute('aria-disabled') == 'true' or \
                                          "opacity: 0.3" in (await p_btn.get_attribute('style') or "")
                            
                            if await p_btn.is_visible() and not is_disabled:
                                print("🚀 返信を送信！")
                                await p_btn.click()
                                await asyncio.sleep(4) # 送信完了を待つ（長め）
                                
                                # 送信成功時のみDBに記録
                                save_replied_user(username)
                                replied_users_db.add(username)
                                
                                replied_count += 1
                                posted = True
                                break
                                
                        if not posted:
                            print("⚠️ 投稿ボタンが押せませんでした。枠外をクリックして閉じます。")
                            await page.keyboard.press("Escape")
                        
                        # スパム判定回避の待機
                        await asyncio.sleep(5)
                            
                except Exception as e:
                    # エラーが起きてもスキップして次へ
                    print(f"⚠️ 処理中にエラー発生: {e}")
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
                    pass
        
        if found_new_reply_on_this_screen:
            idle_scrolls = 0 # 新しい人を見つけたらリセット
        else:
            idle_scrolls += 1
            
        if idle_scrolls >= max_idle_scrolls:
            print("☑️ しばらく新しい未返信コメントが見つかりませんでした。一番下まで到達したと判断して終了します。")
            break
            
        # 画面を少し下へスクロールして新しい要素を読み込む
        print("🔄 少しスクロールして次のコメントを探します...")
        # より小刻みにスクロールして、読み飛ばしを防ぐ
        await page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(2) # 読み込み待ち
            
    print(f"\n🎉 完了: 今回の実行で合計 {replied_count} 件の新規返信を行いました！")


async def main():
    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars'
        ]
        
        if os.path.exists(AUTH_FILE):
            print("🔑 認証情報を使ってThreadsを開きます。")
            # クリップボードの権限を許可して起動（クリップボード入力のため必須）
            browser = await p.chromium.launch(
                headless=False, # 確実に動かすためにヘッドレスを一時オフ（任意）
                channel="chrome", 
                args=browser_args
            )
            # クリップボードのパーミッションを付与
            context = await browser.new_context(
                storage_state=AUTH_FILE,
                permissions=['clipboard-read', 'clipboard-write']
            )
            page = await context.new_page()
            
            # 誤作動で記録された記憶（jsonファイル）を一度強制リセットする（デバッグ用）
            if os.path.exists(REPLIED_USERS_FILE):
                os.remove(REPLIED_USERS_FILE)
                print("🧹 以前の誤作動データをリセットするため、返信済みリストを削除しました。")
            
            try:
                await reply_to_comments(page)
            except Exception as e:
                print(f"⚠️ エラー: {e}")
                print("セッションが切れている可能性があるため、threads_login_manual.py を再実行してください。")
            
            await browser.close()
        else:
            print("⚠️ 認証情報 threads_auth.json がありません。まずは threads_login_manual.py を実行してログインを済ませてください。")

if __name__ == "__main__":
    asyncio.run(main())
