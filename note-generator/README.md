# note記事自動生成システム

Dr.COYASSのnote記事を自動で下書き生成するシステムです。

## 仕組み

1. **GitHub Actions** が毎週月曜9:00 (JST) に自動実行
2. **Claude API** を使って、歯科×音楽のユニークな視点で記事ドラフトを生成
3. 生成された記事は **GitHub Issue** として投稿される
4. Issue内のMarkdownをコピーして、noteに貼り付けて投稿するだけ

## セットアップ

### 1. Anthropic APIキーの設定

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を追加:

- `ANTHROPIC_API_KEY`: Anthropic APIキー（https://console.anthropic.com/ で取得）

### 2. ワークフローの有効化

リポジトリにプッシュすれば自動的にワークフローが有効になります。

### 3. 手動実行

Actions タブ > "Generate note Article Draft" > "Run workflow" で手動実行も可能。

## 記事テーマのカスタマイズ

`generate-note.yml` 内の `topics` 配列を編集して、テーマを追加・変更できます。

## 注意

- 生成された記事は下書きです。内容を確認・編集してからnoteに投稿してください
- APIキーの管理にはご注意ください
