import os
import glob

base_dir = "/Users/coyass/Desktop/TEST/note-articles"
images = [
    "/Users/coyass/.gemini/antigravity/brain/b62d4a26-f4ad-4c42-bfc4-148f1b490741/note_header_part1_1771730873243.png",
    "/Users/coyass/.gemini/antigravity/brain/b62d4a26-f4ad-4c42-bfc4-148f1b490741/note_header_part2_1771730890233.png",
    "/Users/coyass/.gemini/antigravity/brain/b62d4a26-f4ad-4c42-bfc4-148f1b490741/note_header_part3_1771730930622.png",
    "/Users/coyass/.gemini/antigravity/brain/b62d4a26-f4ad-4c42-bfc4-148f1b490741/note_header_part4_1771730950903.png",
    "/Users/coyass/.gemini/antigravity/brain/b62d4a26-f4ad-4c42-bfc4-148f1b490741/note_header_part5_1771730974136.png",
    "/Users/coyass/.gemini/antigravity/brain/b62d4a26-f4ad-4c42-bfc4-148f1b490741/note_header_part6_1771731004913.png"
]

files = sorted(glob.glob(os.path.join(base_dir, "article_0*.md")))

if not files:
    print(f"No match found in {base_dir}")

for i, filepath in enumerate(files):
    if i >= len(images): break
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    if "![アイキャッチ画像]" in "".join(lines[:10]):
        continue
        
    lines.insert(1, f"\n![アイキャッチ画像]({images[i]})\n")
    
    if i > 0:
        separator_count = 0
        for j, line in enumerate(lines):
            if "---" in line:
                separator_count += 1
                if separator_count == 2:
                    paywall = "\n> 💎 **ここから先は有料記事（¥500）です**\n> 診療報酬改定の具体的な対策と収益化ノウハウをすべて公開しています。\n\n"
                    lines.insert(j + 1, paywall)
                    break

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
        print(f"Updated {filepath}")
