import os
import json
import urllib.parse
import urllib.request
from pathlib import Path

# --- 設定エリア ---
# Macの制限を回避するため作業ディレクトリ内に一時保存（後でデスクトップ等に移動可能）
SAVE_DIR = Path("/Users/coyass/kaihatsu/drcoyass-site/集めた論文")
# 既に処理した論文ID（PMID）を記録するファイル
HISTORY_FILE = SAVE_DIR / "processed_pmids.json"
# 取得結果（NotebookLMに渡すデータ）を保存するファイル
TARGET_DATA_FILE = SAVE_DIR / "latest_targets.json"

def init_environment():
    """必要な保存ディレクトリと履歴ファイルを作成する"""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def get_processed_pmids():
    """既に取得済みのPMIDリストを読み込む"""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_processed_pmid(pmid):
    """取得成功したPMIDを履歴に追加して保存する"""
    pmids = list(get_processed_pmids())
    if pmid not in pmids:
        pmids.append(pmid)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(pmids, f, indent=2)

def fetch_europepmc_papers(query, max_results=10):
    """Europe PMCから論文情報を取得する"""
    print(f"🔍 Europe PMCで '{query}' の論文を検索中...(直近{max_results}件)")
    
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded_query}&format=json&resultType=core&pageSize={max_results}"
    
    req = urllib.request.Request(
        search_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get("resultList", {}).get("result", [])
    except Exception as e:
        print(f"❌ 論文データの検索に失敗しました: {e}")
        return []

def download_pdf(pdf_url, save_path):
    """指定されたURLからPDFをダウンロードする"""
    print(f"   ⬇️ PDFをダウンロード中: {pdf_url}")
    try:
        req = urllib.request.Request(
            pdf_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        with urllib.request.urlopen(req, timeout=60) as response, open(save_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"   ✅ 保存完了: {save_path.name}")
        return True
    except Exception as e:
        print(f"   ❌ PDFダウンロード失敗: {e}")
        return False

def main():
    init_environment()
    processed_pmids = get_processed_pmids()
    new_targets = []
    
    query = 'polyphosphate AND (dental OR dentistry OR tooth OR teeth) sort_date:y'
    papers = fetch_europepmc_papers(query, max_results=10)
    
    if not papers:
        print("見つかりませんでした。")
        return
        
    print(f"\n📂 {len(papers)}件の論文が見つかりました（重複や有料除外を判定します）")
    
    for paper in papers:
        pmid = paper.get("pmid", "")
        title = paper.get("title", "No Title")
        
        if not pmid or pmid in processed_pmids:
            continue
            
        print(f"\n📄 新規論文: {title} (PMID: {pmid})")
        
        pdf_url = ""
        fullTextUrlList = paper.get("fullTextUrlList", {}).get("fullTextUrl", [])
        for ftu in fullTextUrlList:
            if ftu.get("documentStyle") == "pdf":
                pdf_url = ftu.get("url", "")
                break
                
        target_info = {
            "pmid": pmid,
            "title": title,
            "abstract": paper.get("abstractText", "No abstract."),
            "type": "",
            "path_or_url": ""
        }
                
        if pdf_url:
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            filename = f"{pmid}_{safe_title.replace(' ', '_')[:50]}.pdf"
            save_path = SAVE_DIR / filename
            
            success = download_pdf(pdf_url, save_path)
            if success:
                target_info["type"] = "pdf_file"
                target_info["path_or_url"] = str(save_path)
                new_targets.append(target_info)
                save_processed_pmid(pmid)
            else:
                abstract_url = f"https://europepmc.org/article/MED/{pmid}"
                print(f"   ⚠️ PDF取得失敗のため、Abstract URLを記録します: {abstract_url}")
                target_info["type"] = "url"
                target_info["path_or_url"] = abstract_url
                new_targets.append(target_info)
                save_processed_pmid(pmid)
        else:
            abstract_url = f"https://europepmc.org/article/MED/{pmid}"
            print(f"   🔒 有料/PDFリンクなし。Abstract URLを記録します: {abstract_url}")
            target_info["type"] = "url"
            target_info["path_or_url"] = abstract_url
            new_targets.append(target_info)
            save_processed_pmid(pmid)
            
    print("\n" + "="*50)
    if new_targets:
        print(f"🎉 今回新しく {len(new_targets)} 件の論文ソースを取得・登録しました！")
        with open(TARGET_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_targets, f, ensure_ascii=False, indent=2)
        print(f"✅ NotebookLM用の情報ファイルを更新しました: {TARGET_DATA_FILE}")
    else:
        print("💡 新しい論文はありませんでした。（全て取得済みです）")

if __name__ == "__main__":
    main()
