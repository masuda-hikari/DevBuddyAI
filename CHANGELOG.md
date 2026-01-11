# Changelog

本プロジェクトのすべての重要な変更を記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.0.0/)に従い、
[セマンティック バージョニング](https://semver.org/lang/ja/)を採用しています。

## [0.1.0] - 2026-01-12

### 追加機能
- **AIコードレビュー**: コード変更をAIが分析し、バグ・スタイル違反・ドキュメント不足を指摘
- **テスト自動生成**: 関数/クラスからユニットテストを自動生成（pytest形式）
- **バグ修正提案**: 失敗テストや既知バグに対する修正案を自動提示
- **自己検証ループ**: 生成したテスト/修正を自動実行・検証（最大3回リトライ）

### 対応言語
- Python（flake8, mypy連携）
- JavaScript/TypeScript（ESLint, tsc連携）
- Rust（clippy, cargo check連携）
- Go（go vet, staticcheck, golangci-lint連携）

### CLI機能
- `devbuddy review <file>` - コードレビュー実行
- `devbuddy testgen <file>` - テスト自動生成
- `devbuddy fix <file>` - バグ修正提案
- `devbuddy license` - ライセンス管理
- `devbuddy billing` - 課金管理
- `devbuddy config` - 設定管理
- `devbuddy server` - Webhookサーバー管理

### 出力形式
- Text（デフォルト）
- JSON（CI/CD統合向け）
- Markdown（ドキュメント向け）

### 設定
- `.devbuddy.yaml` による設定ファイル対応
- CLI引数 > 設定ファイル > デフォルト値の優先順位

### GitHub連携
- PR自動レビュー GitHub Action
- GitHub Marketplace公開対応（action.yml）
- Check Run作成、PRコメント自動更新

### 課金システム
- FREE/PRO/TEAM/ENTERPRISEプラン
- Stripe Checkout/Webhook連携
- 日本円価格設定（Pro: ¥1,980/月、Team: ¥9,800/月）

### VSCode拡張
- コードレビュー/テスト生成/バグ修正コマンド
- 問題一覧/生成テスト/利用状況ツリービュー
- キーボードショートカット対応

### クラウドデプロイ
- Docker対応（マルチステージビルド）
- Railway/Render/Fly.io設定ファイル

### ドキュメント
- ランディングページ（GitHub Pages）
- プライバシーポリシー/利用規約/特定商取引法表記
- MkDocs APIリファレンス
- 貢献ガイド/セキュリティポリシー

### 品質
- テストカバレッジ: 85%（601件テスト）
- flake8: エラーゼロ
- mypy: エラーゼロ（24ソースファイル）
