import subprocess
import sys
import time
from pathlib import Path

# ==========================================
# 🌐 全SNS一括自動投稿スクリプト
# ==========================================
# 目的: 生成されたスレッド原稿を確認後、
#      X、Threads、Note、Facebookへ順次自動投稿（下書き保存）を行います。
# 前提: 各プラットフォームのログインが終わっていること。
#      (twitter_auth.json, threads_auth.json, 
#       note_auth.json, facebook_auth.json が存在すること)
# ==========================================

SCRIPTS = [
    ("X (Twitter)", "twitter_auto_post.py"),
    ("Threads", "threads_auto_post.py"),
    ("Note (下書き)", "note_auto_post.py"),
    ("Facebook", "facebook_auto_post.py")
]

def main():
    print("=========================================")
    print("🚀 全SNSプラットフォームへの自動投稿を開始します！")
    print("=========================================")
    
    # 実行前に認証ファイルの存在確認
    missing_auth = []
    auth_files = {
        "X (Twitter)": "twitter_auth.json",
        "Threads": "threads_auth.json",
        "Note (下書き)": "note_auth.json",
        "Facebook": "facebook_auth.json"
    }
    
    for name, auth_file in auth_files.items():
        if not Path(auth_file).exists():
            missing_auth.append((name, auth_file))
            
    if missing_auth:
        print("\n⚠️ 以下のプラットフォームの認証ファイルが見つかりません。")
        for name, file in missing_auth:
            print(f" - {name} (ファイル: {file})")
        print("\n各手動ログイン用スクリプトを実行してログインを済ませてから再実行してください。")
        response = input("強制的に処理を続行しますか？ (y/n): ")
        if response.lower() != 'y':
            print("処理を中止します。")
            sys.exit(1)
            
    print("\n順次投稿スクリプトを呼び出します...")
    
    for name, script_name in SCRIPTS:
        if not Path(script_name).exists():
             print(f"⚠️ スクリプトが見つかりません: {script_name} - スキップします")
             continue
             
        print(f"\n▶️ [{name}] の投稿処理を開始します... ({script_name})")
        
        try:
            # subprocessで各スクリプトを順次実行する
            result = subprocess.run([sys.executable, script_name], check=True)
            print(f"✅ [{name}] の処理が正常に終了しました！")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ [{name}] の処理中にエラーが発生しました。スクリプトが異常終了しました。(終了コード: {e.returncode})")
        except Exception as e:
            print(f"❌ [{name}] の実行に失敗しました: {e}")
            
        # 次の処理へ行く前に少し待機
        time.sleep(3)
        
    print("\n=========================================")
    print("🎉 すべての自動投稿スクリプトの呼び出しが完了しました！")
    print("   各SNSの実際の投稿内容をご確認ください。")
    print("   Noteは「下書き」保存になっているので、チェックして手動で公開してください。")
    print("=========================================")

if __name__ == "__main__":
    main()
