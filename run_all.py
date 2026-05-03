import subprocess
import time
import os
import sys

# ==========================================
# 🚀 論文処理フルオートメーションスクリプト
# ==========================================
# 1. PubMedから論文取得 (pubmed_fetcher.py)
# 2. NotebookLMへアップロード＆スレッド原案生成 (notebooklm_auto_upload.py)
#    (※論文取得がない日などは generate_daily_topic.py が発動)
# 3. X (Twitter) へ自動投稿 (twitter_auto_post.py)
# 4. Threads へ自動投稿 (threads_auto_post.py)
# 5. Threads のコメントへ自動返信 (threads_auto_reply.py)
# 6. Note へ自動下書き投稿 (note_auto_post.py)

def run_script(script_name):
    print(f"\n=======================================================")
    print(f"▶️ 実行開始: {script_name}")
    print(f"=======================================================")
    
    # 実行
    result = subprocess.run([sys.executable, script_name], capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ エラー: {script_name} の実行中に致命的なエラーが発生しました。")
        print("全体の自動化処理を中断します。")
        sys.exit(1)
        
    print(f"✅ {script_name} の実行が完了しました。\n")
    time.sleep(2)  # スクリプト間に少し間隔を空ける

def main():
    print("🌟 論文自動処理パイプラインを開始します 🌟")
    
    # 論文取得とNotebookLM処理
    scripts_phase1 = [
        "pubmed_fetcher.py",
        "notebooklm_auto_upload.py"
    ]
    
    for script in scripts_phase1:
        if os.path.exists(script):
            run_script(script)
        else:
            print(f"⚠️ 警告: スクリプト '{script}' が見つかりません。スキップします。")
            
    # もしここで latest_thread_draft.txt が（空、または存在し）なければ、
    # ペルソナAIによる日常投稿生成にフェールオーバーする
    draft_file = "latest_thread_draft.txt"
    needs_daily_topic = False
    
    if not os.path.exists(draft_file):
        needs_daily_topic = True
    else:
        # ファイルが空かチェック
        with open(draft_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                needs_daily_topic = True
                
    if needs_daily_topic:
        print("\nℹ️ 論文に基づく新しいドラフトがありません。Dr.コヤス先生の日常テーマ（AIペルソナ）投稿を生成します...")
        if os.path.exists("generate_daily_topic.py"):
            run_script("generate_daily_topic.py")
        else:
            print("⚠️ generate_daily_topic.py が見つからないため、投稿をスキップします。")
            
    # 生成されたドラフトがいずれにせよ存在する場合は、投稿フローへ進む
    if os.path.exists(draft_file):
        with open(draft_file, 'r', encoding='utf-8') as f:
            if f.read().strip():
                # 投稿系スクリプト群
                scripts_phase2 = [
                    "twitter_auto_post.py",
                    "threads_auto_post.py",
                    "threads_auto_reply.py",
                    "note_auto_post.py"
                ]
                
                for script in scripts_phase2:
                    if os.path.exists(script):
                        run_script(script)
                    else:
                        print(f"⚠️ 警告: スクリプト '{script}' が見つかりません。スキップします。")
            else:
                print("🚫 ドラフトファイルが空のため、投稿処理を中止します。")
    else:
        print("🚫 ドラフトファイルが作成されなかったため、投稿処理を中止します。")
        
    print("\n🎉 全ての自動化プロセスが正常に完了しました！🎉")
    print("※ XとThreadsへの投稿、およびNoteへの下書き保存が完了しているか、各プラットフォームでご確認ください。")

if __name__ == "__main__":
    main()
