# 変更履歴

## [0.1.0] - 2026-01-11

### 追加

- **コアエンジン**
  - AIコードレビュー機能
  - テスト自動生成機能（自己検証ループ付き）
  - バグ修正提案機能
  - 出力フォーマッター（Text/JSON/Markdown）

- **静的解析**
  - Python: AST解析 + flake8/mypy連携
  - JavaScript/TypeScript: ESLint/tsc連携
  - Rust: clippy/cargo check連携
  - Go: go vet/staticcheck/golangci-lint連携

- **LLM連携**
  - Claude API対応
  - OpenAI API対応
  - プロンプトテンプレート

- **外部連携**
  - GitHub API連携（PR差分取得、コメント投稿）
  - ローカルGit操作

- **CLI**
  - `devbuddy review` - コードレビュー
  - `devbuddy testgen` - テスト生成
  - `devbuddy fix` - バグ修正提案
  - `devbuddy config` - 設定管理
  - `devbuddy auth` - 認証設定

- **設定ファイル**
  - `.devbuddy.yaml` 対応
  - CLI引数 > 設定ファイル > デフォルト値の優先順位

- **ドキュメント**
  - ランディングページ
  - プライバシーポリシー
  - 利用規約
  - 特定商取引法に基づく表記

- **CI/CD**
  - GitHub Actions（lint/test/build）
  - PyPI自動公開ワークフロー
  - GitHub Pagesデプロイワークフロー
