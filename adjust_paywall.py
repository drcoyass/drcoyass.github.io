import os
import glob

base_dir = "/Users/coyass/Desktop/TEST/note-articles"
files = sorted(glob.glob(os.path.join(base_dir, "article_0*.md")))

paywall_text = "> 💎 **ここから先は有料記事（¥500）です**\n> 診療報酬改定の具体的な対策と収益化ノウハウをすべて公開しています。\n\n"

for filepath in files:
    # article_01は無料公開用コンテンツとしての性質が強いためスキップ、または別途処理
    if "article_01" in filepath:
        continue
        
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # スライド画像の初出インデックスを探す
    first_slide_idx = -1
    for i, line in enumerate(lines):
        if "![ " in line or "![" in line and "slides_wm/slide_" in line:
            first_slide_idx = i
            break
            
    # paywallのインデックスを探す
    paywall_idx = -1
    for i, line in enumerate(lines):
        if "💎 **ここから先は有料記事" in line:
            paywall_idx = i
            break
            
    if first_slide_idx != -1:
        # もしPaywallが存在し、かつスライドより「後」にあるなら、Paywallを古い位置から削除してスライドの直前に移動
        if paywall_idx != -1 and paywall_idx > first_slide_idx:
            # 既存のPaywall行を削除（通常3行分：テキスト＋テキスト＋空行）
            # 後ろから削除しないとインデックスがずれるが、ここではスライド前に新しく入れる処理を先に行う
            print(f"Moving paywall in {filepath} to index {first_slide_idx}")
            lines.insert(first_slide_idx, "\n" + paywall_text)
            
            # 再度paywall_idxを探して削除
            # indexはずれているため再検索
            for i, line in enumerate(lines[first_slide_idx+1:], start=first_slide_idx+1):
                if "💎 **ここから先は有料記事" in line:
                    del lines[i:i+3]
                    break
                    
        elif paywall_idx == -1:
            # Paywallが存在しない場合は、最初のスライドの直前に挿入
            print(f"Inserting paywall in {filepath} at index {first_slide_idx}")
            lines.insert(first_slide_idx, "\n" + paywall_text)
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
print("Paywall and slide positions have been successfully adjusted.")
