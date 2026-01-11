# DevBuddyAI - VSCode拡張

AI開発者支援ツール。コードレビュー、テスト生成、バグ修正提案をエディタ内で実行。

## 機能

### コードレビュー
- **ファイル全体のレビュー**: `Ctrl+Shift+R` (Mac: `Cmd+Shift+R`)
- **選択範囲のレビュー**: 右クリック → DevBuddyAI: コードレビュー

### テスト生成
- **テスト生成**: `Ctrl+Shift+T` (Mac: `Cmd+Shift+T`)
- pytest, unittest, jest, mocha, cargo-test, go-test対応

### バグ修正提案
- **修正提案**: `Ctrl+Shift+F` (Mac: `Cmd+Shift+F`)
- コードを選択して修正提案を取得

## 対応言語
- Python
- JavaScript / TypeScript
- Rust
- Go

## インストール

### Marketplaceから（推奨）
1. VSCode拡張機能を開く (`Ctrl+Shift+X`)
2. "DevBuddyAI" で検索
3. インストール

### 手動インストール
```bash
# vsixパッケージをダウンロード
# VSCode: Extensions → ... → Install from VSIX
```

## 設定

### APIキー設定
1. コマンドパレット (`Ctrl+Shift+P`)
2. "DevBuddyAI: APIキー設定" を選択
3. APIキーを入力

または環境変数で設定:
```bash
export DEVBUDDY_API_KEY=your_api_key
```

### 設定オプション

| 設定 | 説明 | デフォルト |
|------|------|-----------|
| `devbuddy.apiKey` | APIキー | - |
| `devbuddy.model` | AIモデル | `claude-3-sonnet` |
| `devbuddy.severity` | レビュー厳格さ | `medium` |
| `devbuddy.autoReviewOnSave` | 保存時自動レビュー | `false` |
| `devbuddy.testFramework` | テストフレームワーク | `pytest` |
| `devbuddy.showInlineIssues` | インライン表示 | `true` |
| `devbuddy.cliPath` | CLIパス | - |
| `devbuddy.serverUrl` | サーバーURL（自己ホスト用） | - |

### 設定例 (settings.json)
```json
{
  "devbuddy.model": "claude-3-sonnet",
  "devbuddy.severity": "high",
  "devbuddy.autoReviewOnSave": true,
  "devbuddy.testFramework": "pytest"
}
```

## キーボードショートカット

| 機能 | Windows/Linux | Mac |
|------|--------------|-----|
| ファイルレビュー | `Ctrl+Shift+R` | `Cmd+Shift+R` |
| テスト生成 | `Ctrl+Shift+T` | `Cmd+Shift+T` |
| 修正提案 | `Ctrl+Shift+F` | `Cmd+Shift+F` |

## サイドバー

DevBuddyAIアイコンをクリックすると以下が表示:
- **問題一覧**: 検出された問題
- **生成テスト**: 生成されたテスト
- **利用状況**: API利用状況

## ライセンス

MIT License

## サポート

- [GitHub Issues](https://github.com/masuda-hikari/DevBuddyAI/issues)
- [ドキュメント](https://masuda-hikari.github.io/DevBuddyAI/)
