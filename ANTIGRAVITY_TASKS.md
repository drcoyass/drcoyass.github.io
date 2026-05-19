# Antigravity Manager View 用タスク指示書

> drcoyass-site のAEO最適化を Antigravity の複数エージェントで並行進める用
> 作成日: 2026-05-17 (Claude による初期実装後)

---

## 1. すでに完了した実装 (Claude 側で実施済み)

下記は **すでに drcoyass-site に commit 待ちの状態**で配置済み:

1. ✅ `robots.txt` — AI クローラ (GPTBot/ClaudeBot/PerplexityBot 等 20+) を明示許可
2. ✅ `index.html` の `<head>` 内に Schema.org JSON-LD を4ブロック追加
   - Physician (Dr.COYASS の医療プロフィール、論文・学会・受賞・SNS全部入り)
   - MedicalBusiness/Dentist/LocalBusiness (中目黒コヤス歯科)
   - FAQPage (患者・歯科医師がAIに聞きそうな10問)
   - WebSite (サイト全体のメタ)
3. ✅ `about-coyass.html` — Dr.COYASS のファクトシート (14セクション、AbouPage Schema 付き)
4. ✅ `index.html` のナビバーに `About` リンク追加 (/about-coyass.html)
5. ✅ `sitemap.xml` に /about-coyass.html を追加

バックアップ済み: `*.bak.20260517` ファイルあり (確認後に削除可)

---

## 2. Antigravity Manager View で並行実行する5タスク

### Agent 1: index.html のフッターに about-coyass へのカード追加
```
ファイル: /Users/coyass/kaihatsu/drcoyass-site/index.html

タスク:
"#contact" セクションの直前 (Connect / LINKS 見出しの上付近) に、
"Profile Facts" という新セクションを追加してください。

要件:
- 既存のサイトテイスト (gold/dark カラー、Bebas Neue / Noto Sans JP) に統一
- カード形式で about-coyass.html へのリンク
- カード内に下記の要素を含む:
  - 「歯科医師・歯学博士・分割ポリリン酸研究会 会長」(役職)
  - 主要論文: Ultraphosphate (Dental Material J 2014)
  - 8年実臨床: 知覚過敏 <1%
  - 「フルプロフィール → /about-coyass.html」CTAボタン

完了条件:
- index.html を編集
- ローカルプレビューで表示崩れなし
- about-coyass.html へのリンクが動作
```

### Agent 2: 既存メディア掲載ページ /media.html を新設
```
タスク:
/Users/coyass/kaihatsu/drcoyass-site/media.html を新規作成。

含める第三者メディア (実在を確認済み、各リンクに canonical 表記):
1. DENTAL REPORT — https://dentalreport.jp/shinbi/ceramic/koyasu-dc/
2. Doctors File — https://doctorsfile.jp/h/189635/
3. Tokyo Doctors — https://tokyo-doctors.com/dentalList/57950
4. Tokyo Doctors 独自取材記事 — https://tokyo-doctors.com/dentalList/57950/interview
5. WHITE CROSS — https://www.whitecross.co.jp/doctor-introductions/view/598
6. Seeker Dental インタビュー — https://seeker-dental.com/info/0521/
7. Teeeeth! メンバー紹介 — https://www.teeeeth.jp/dr_coyass.html
8. ORTC 講師紹介 — https://ortc.jp/teachers/73
9. 歯科医療総研 講師ページ — https://shika-soken.com/products/list?category_id=454
10. 歯科セミナー1D 講師ページ — https://oned.jp/biographies/1738

Schema.org:
- ItemList / Article schema を含めて、各メディアを構造化

完了条件:
- media.html が存在し、index.html / about-coyass.html からリンクされている
- sitemap.xml に追加
```

### Agent 3: 患者向け FAQ ページ /faq.html
```
タスク:
/Users/coyass/kaihatsu/drcoyass-site/faq.html を新規作成。

患者がAIに聞きそうな質問30問:

【ポリリン酸ホワイトニング】
1. ポリリン酸ホワイトニングって普通のホワイトニングと何が違う?
2. 痛くないって本当?
3. 1回でどれくらい白くなる?
4. 何回くらい通う?
5. 値段はいくら?
6. 効果はどれくらい持つ?
7. 妊娠中・授乳中はできる?
8. 子供でもできる?
9. メンテナンスは必要?
10. 他のホワイトニングを既にやってる人でもできる?

【中目黒コヤス歯科】
11. 予約はどう取る?
12. 営業時間は?
13. 駐車場はある?
14. 初診で何を聞かれる?
15. 保険は使える?
16. 支払い方法は?
17. キッズスペースはある?
18. オンライン相談はある?
19. 通院期間中の食事制限は?
20. 治療後の生活注意は?

【Dr.COYASS について】
21. 院長はどんな人?
22. なぜラッパー?
23. 学会発表はしてる?
24. 研究はしてる?
25. メディア出演実績は?

【自由診療・自費】
26. 自費の支払い方法は? (デンタルローン等)
27. セラミックとホワイトニングはどっちが先?
28. 全顎セラミックの相場は?
29. インビザラインも対応してる?
30. 院内ホワイトニングと自宅ホワイトニングはどっちがいい?

各回答は150-300字、固有名詞・数字・出典を必ず含める。
FAQPage Schema を付与。
```

### Agent 4: クリニック側 dr-coyass.com の AEO 改修案
```
dr-coyass.com は別ドメイン (おそらく Jimdo か似たSaaS で構築) の可能性。
編集権限が drcoyass.com と別の場合、JimdoのHTML編集枠から以下を埋め込む案を準備:

タスク:
/Users/coyass/kaihatsu/drcoyass-site/DR_COYASS_CLINIC_AEO_PATCH.md を作成し、
dr-coyass.com に追加すべき:
1. robots.txt (AIクローラ許可) — クリニック側に Jimdo の robots.txt 編集機能がある場合
2. Schema.org JSON-LD (MedicalBusiness/Dentist) — HTML埋め込み枠に貼り付け用
3. FAQPage の患者向け10問版 — HTML埋め込み

完了条件:
- パッチファイルが手順書として完成
- Jimdo 等のCMS制限下でも適用可能な指示
```

### Agent 5: Google Search Console / Bing Webmaster の再 submit と
```
タスク (実行は人間が、準備は Agent が):

1. Google Search Console:
   - sitemap.xml を再送信
   - URL Inspection で /about-coyass.html を手動 index 申請
   - Structured Data Report で新JSON-LDの認識を確認

2. Bing Webmaster Tools:
   - sitemap.xml を送信 (まだなら登録)
   - IndexNow API で /about-coyass.html を即時通知

3. IndexNow Key 設定:
   - drcoyass.com/{KEY}.txt を配置 (Bing/Yandex 用の高速インデックス)

Agent が準備するもの:
- ./SEO_SUBMISSION_PLAYBOOK.md に手順とチェックリストをまとめる
- IndexNow Key ファイル (任意の英数32文字)
```

---

## 3. このディレクトリでの git commit 推奨手順

```bash
cd ~/kaihatsu/drcoyass-site

# 状態確認
git status

# 変更内容の diff を確認 (バックアップとの差分)
git diff --stat

# 段階的にコミット
git add robots.txt
git commit -m "AEO: AI search crawlers (GPTBot/ClaudeBot/PerplexityBot etc.) explicitly allowed"

git add sitemap.xml
git commit -m "AEO: add /about-coyass.html to sitemap"

git add about-coyass.html
git commit -m "AEO: add comprehensive fact sheet page (/about-coyass.html) with AboutPage schema"

git add index.html
git commit -m "AEO: replace minimal Person schema with 4 full JSON-LD blocks (Physician/MedicalBusiness/FAQPage/WebSite) + nav link to About"

# ローカルプレビュー
# Antigravity の Live Preview 機能でブラウザ確認

# 公開 (GitHub Pages の場合 push で自動 deploy)
git push origin main

# Google Search Console で sitemap 再送信
```

---

## 4. デプロイ後 24時間以内のチェック

- [ ] https://drcoyass.com/robots.txt が新ファイルに更新されているか
- [ ] https://drcoyass.com/sitemap.xml に /about-coyass.html が含まれているか
- [ ] https://drcoyass.com/about-coyass.html がアクセス可能か (HTTP 200)
- [ ] https://drcoyass.com/ のソースで JSON-LD 4ブロックが確認できるか
- [ ] [Google Rich Results Test](https://search.google.com/test/rich-results) で
      Physician / MedicalBusiness / FAQPage / WebSite が valid 表示されるか
- [ ] [Schema.org Validator](https://validator.schema.org/) で warnings 0 か
- [ ] PageSpeed Insights でパフォーマンス劣化していないか (新ページが軽量か)

---

## 5. デプロイ後 1週間以内のチェック

- [ ] ChatGPT (Search モード) で「Dr.COYASS とは」「中目黒 ポリリン酸 おすすめ」と聞いて
      drcoyass.com が citation source として出るか
- [ ] Perplexity で「分割ポリリン酸研究会 会長」と検索して Dr.COYASS が出るか
- [ ] Claude (with Web) で「ポリリン酸 ホワイトニング 知覚過敏」と聞いて引用されるか
- [ ] Google Knowledge Graph に「Dr.COYASS」または「中目黒コヤス歯科」のサイドパネルが出るか
- [ ] Bing Chat / Copilot でも同様の確認

---

## 6. 今後追加で実装したいページ (優先度順)

1. `/faq.html` — 患者向けFAQ 30問 (Agent 3 で生成)
2. `/media.html` — メディア掲載集約 (Agent 2 で生成)
3. `/research.html` — 論文・研究業績一覧 (Schema.org ScholarlyArticle)
4. `/seminar-history.html` — セミナー・講演履歴 (Schema.org Event)
5. `/services/polyphosphate-whitening.html` — ポリリン酸ホワイトニング詳細ページ (MedicalProcedure)
6. `/blog/` または `/note-cross-post/` — note 記事のクロスポスト (canonical: note URL)

---

## 7. 関連リソース

- 戦略全体: ../Desktop/TEST/Blog\&X/AEO_OPTIMIZATION.md
- 共通ベース文章: ../Desktop/TEST/Blog\&X/AEO_BASE_TEXTS.md
- プロフィール権威版: ../Desktop/TEST/Blog\&X/PROFILE_AUTHORITATIVE.md
