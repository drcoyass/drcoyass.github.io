import asyncio
import os
import random
import re
import json
from pathlib import Path
from playwright.async_api import async_playwright

# ==========================================
# 🚀 X (Twitter) 収益化特化型・自動エンゲージメントボット
# ==========================================
# 目的: インプレッション500万を最短突破するための「高質リプライ」自動生成・送信
# ==========================================

AUTH_FILE = "/Users/coyass/kaihatsu/drcoyass-site/twitter_auth.json"
REPLY_LOG_FILE = "/Users/coyass/kaihatsu/drcoyass-site/replied_logs.json"

# コヤス様の「型」アルゴリズム
COYASS_MODES = [
    {
        "name": "Medical DX / Expert",
        "keywords": ["歯科", "医療", "働き方改革", "DX", "経営", "クリニック"],
        "prompt": "医療現場の非効率をAIで解決する実務家として、論理的かつ少し辛口に「属人性の排除」を語れ。"
    },
    {
        "name": "AI / Tech / Visionary",
        "keywords": ["AI", "Claude", "GPT", "エージェント", "自動化", "2026年"],
        "prompt": "『デモより実務』をモットーとし、Antigravity等のツールを使いこなす歯科医として、技術の『身体拡張』をクールに語れ。"
    },
    {
        "name": "Culture / Music / Aesthetic",
        "keywords": ["音楽", "KREVA", "ヒップホップ", "美学", "創作", "デジタル"],
        "prompt": "感性と論理のハイブリッドとして、計算を超えた『美学』の重要性を、音楽制作と医療の共通点を通じて語れ。"
    }
]

def load_replied_logs():
    if os.path.exists(REPLY_LOG_FILE):
        with open(REPLY_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_replied_log(logs):
    with open(REPLY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

async def generate_coyass_reply(post_content):
    """
    Antigravity(LLM)へのプロンプト生成関数（本来はここでAPIを叩くが、
    ここではスクリプト内に内蔵されたロジックでコヤス様風の文面を生成する）
    """
    # 実際の実装ではここでLLMにpost_contentを渡して生成させる
    # 今回は簡略化のため、パターンの組み合わせで生成（後でAntigravityが直接書き換えることも可能）
    
    # 投稿内容からキーワードを抽出
    selected_mode = COYASS_MODES[1] # デフォルトはAIモード
    for mode in COYASS_MODES:
        if any(k in post_content for k in mode["keywords"]):
            selected_mode = mode
            break
            
    # モードに応じた「コヤス的」反応のテンプレート
    responses = {
        "Medical DX / Expert": [
            f"医療現場の{post_content[:10]}...等の非効率は、もはや気合じゃ解決しない。本質は『属人性の排除』。僕が歯科経営にAIをフル装備してるのも、誰が担当しても最高品質を担保するため。属人性への依存は、患者さんへの不義理にもなりかねないですからね。",
            "結局、DXが進まないのは思考停止が原因。現場にAIを放り込むと、一瞬で景色が変わる。歯科医として『削って埋める』以外の価値をどう作るか、そこに集中できる環境作りが急務です。"
        ],
        "AI / Tech / Visionary": [
            "デモ動画で終わる人と、実務で回す人の差がここ。AIエージェントによる『身体拡張』はもうSFじゃない。僕の環境ではAntigravityが24時間コードを書き換えてるけど、この加速感を知ると元の世界には戻れないですね。",
            "2026年問題への答えは、技術による『時間の錬金術』にある。AIをツールじゃなく『相棒』としてどこまで信じられるか。そこが未来への分岐点になるはず。"
        ],
        "Culture / Music / Aesthetic": [
            "音楽も医療も、最後は『美学』があるかどうか。数値化できない先の感動をどうデザインするか、毎日格闘してます。KREVAさんのビートのように、計算を超えた説得力をデジタルで表現したい。",
            "論理（AI）と感性（音楽）のハイブリッド。これがこれからのクリエイティブの正解だと思う。歯科医をやりながらビートを刻むのも、僕の中では完全に一本の線で繋がってる。"
        ]
    }
    
    reply = random.choice(responses[selected_mode["name"]])
    return reply[:140] # 140文字制限

async def post_reply(page, tweet_url, reply_text):
    print(f"🔗 ターゲット投稿へ移動: {tweet_url}")
    try:
        await page.goto(tweet_url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # リプライボックスを探す（複数のセレクタを試行）
        reply_box_selectors = [
            'div[data-testid="tweetTextarea_0"]',
            'div[role="textbox"]',
            '.public-DraftEditor-content'
        ]
        
        reply_box = None
        for selector in reply_box_selectors:
            try:
                el = await page.wait_for_selector(selector, timeout=5000)
                if el:
                    reply_box = el
                    break
            except:
                continue
        
        if not reply_box:
            raise Exception("リプライ入力エリアが見つかりませんでした。")

        # 入力エリアをクリック（force=Trueでマスクを突破）
        await reply_box.click(force=True)
        await asyncio.sleep(1)
        
        print(f"✍️ リプライ入力中: {reply_text[:20]}...")
        await page.keyboard.type(reply_text, delay=random.randint(50, 100))
        await asyncio.sleep(1)
        
        # 送信ボタン
        send_btn = await page.get_by_test_id("tweetButtonInline")
        if not await send_btn.is_visible():
            send_btn = await page.get_by_text("返信").first
            
        await send_btn.click(force=True)
        await asyncio.sleep(3)
        print("✅ 送信完了")
        return True
    except Exception as e:
        print(f"❌ 返信エラー: {e}")
        return False

async def main():
    print("🚀 X-Monetization-Bot 起動")
    replied_logs = load_replied_logs()
    
    async with async_playwright() as p:
        browser_args = ['--disable-blink-features=AutomationControlled', '--disable-infobars']
        
        if not os.path.exists(AUTH_FILE):
            print("⚠️ 認証情報がありません。先に twitter_auto_post.py でログインしてください。")
            return
            
        print("🔑 セッションをロード中...")
        browser = await p.chromium.launch(headless=True, channel="chrome", args=browser_args)
        context = await browser.new_context(storage_state=AUTH_FILE)
        page = await context.new_page()
        
        # ターゲット収集: ホームタイムラインのスクロール
        print("🔎 バズ投稿（インプ源）を探索中...")
        await page.goto("https://x.com/home", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        targets = []
        for _ in range(5): # 5回転スクロール
            # ツイート要素を全取得
            tweets = await page.query_selector_all('article[data-testid="tweet"]')
            for tweet in tweets:
                try:
                    # テキスト取得
                    text_el = await tweet.query_selector('div[data-testid="tweetText"]')
                    text = await text_el.inner_text() if text_el else ""
                    
                    # リンク取得
                    link_el = await tweet.query_selector('a[href*="/status/"]')
                    link = await link_el.get_attribute("href") if link_el else ""
                    full_url = f"https://x.com{link}"
                    
                    # すでにリプライ済みならスキップ
                    if full_url in replied_logs:
                        continue
                        
                    # 表示回数（インプ数）の簡易チェック（あれば）
                    # XのUI上、表示回数は 'analytics' リンク等に含まれることが多い
                    # ここでは一旦「見つけたものから順に」5件選定
                    if link and text and len(targets) < 5:
                        targets.append({"url": full_url, "content": text})
                except:
                    continue
            
            await page.mouse.wheel(0, 1500)
            await asyncio.sleep(2)
        
        print(f"🎯 {len(targets)}件のターゲットをロックオンしました。")
        
        for target in targets:
            reply_text = await generate_coyass_reply(target["content"])
            success = await post_reply(page, target["url"], reply_text)
            if success:
                replied_logs.append(target["url"])
            
            # レート制限回避のための休憩
            wait_time = random.randint(60, 180)
            print(f"☕ 次の投稿まで {wait_time}秒 待機します...")
            await asyncio.sleep(wait_time)
            
        save_replied_log(replied_logs)
        await browser.close()
        print("🏁 全ての処理を完了しました。5Mインプレッションへ一歩前進です。")

if __name__ == "__main__":
    asyncio.run(main())
