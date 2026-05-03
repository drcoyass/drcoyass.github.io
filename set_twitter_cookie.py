import json
import sys
import os

AUTH_FILE = "twitter_auth.json"

def create_auth_state(auth_token):
    # Playwrightのstorage_stateフォーマットに合わせてCookieを構築
    cookies = [
        {
            "name": "auth_token",
            "value": auth_token,
            "domain": ".x.com",
            "path": "/",
            "expires": 4102444800, # 2100年
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        },
        {
            "name": "ct0",
            "value": "dummy_ct0_value_for_bypass", # 値は不正確でも存在することが重要
            "domain": ".x.com",
            "path": "/",
            "expires": 4102444800,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax"
        }
    ]
    
    # x.com用のstorage_stateのベース構造
    state = {
        "cookies": cookies,
        "origins": []
    }
    
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        
    print(f"✅ セッション情報を {AUTH_FILE} に生成しました！")
    print("これでもうログイン画面を突破する必要はありません。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python3 set_twitter_cookie.py <あなたのauth_token>")
        sys.exit(1)
        
    token = sys.argv[1]
    create_auth_state(token)
