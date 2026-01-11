# DevBuddyAI

**AI搭載の開発アシスタント** - コードレビュー、テスト生成、バグ修正を行うあなたのAIペアプログラマー。

[English](README.md) | **日本語**

## 概要

DevBuddyAIは、最先端のAI技術を活用して開発ライフサイクル全体をサポートします：

- **自動コードレビュー**: コード品質、潜在的なバグ、スタイル問題を即座にフィードバック
- **テスト自動生成**: 関数から包括的なユニットテストを自動生成
- **バグ修正提案**: 失敗したテストや既知のバグに対するAI駆動の修正提案
- **マルチプラットフォーム対応**: CLI、GitHub Actions、VSCode拡張で利用可能

## 機能

### コードレビュー
```bash
$ devbuddy review src/mycode.py

DevBuddyAI コードレビュー結果:
================================

[警告] 23行目: 'data' が None の可能性あり
  提案: data.items() にアクセスする前にnullチェックを追加

[スタイル] 45行目: 関数名 'processData' は snake_case を使用すべき
  提案: 'process_data' にリネーム

[バグ] 67行目: count == 0 の場合ゼロ除算の可能性
  提案: ガード句を追加: if count == 0: return 0

サマリー: バグ1件、警告1件、スタイル問題1件
```

### テスト生成
```bash
$ devbuddy testgen src/calculator.py --function add

生成されたテストファイル: tests/test_calculator.py

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 5) == 5

def test_add_floats():
    assert add(1.5, 2.5) == 4.0

生成されたテストを実行中... 4件すべて合格！
```

### バグ修正提案
```bash
$ devbuddy fix tests/test_api.py

失敗テスト分析結果:
====================

[test_get_user_by_id] FAILED
エラー: KeyError: 'email'

AI修正提案:
-----------
user = {"name": name}
+user = {"name": name, "email": "default@example.com"}

信頼度: 85%
カテゴリ: バグ修正
```

### GitHub連携
DevBuddyAIはプルリクエストに自動でコードレビューコメントを投稿します。

## インストール

```bash
pip install devbuddy-ai
```

ソースからインストール:
```bash
git clone https://github.com/masuda-hikari/DevBuddyAI.git
cd DevBuddyAI
pip install -e .
```

## クイックスタート

### 1. APIキーの設定
```bash
export DEVBUDDY_API_KEY=your_api_key_here
# または
devbuddy auth
```

### 2. コードレビュー
```bash
devbuddy review path/to/your/code.py
```

### 3. テスト生成
```bash
devbuddy testgen path/to/your/code.py
```

### 4. バグ修正提案
```bash
devbuddy fix path/to/failing_tests.py
```

## 設定

プロジェクトルートに `.devbuddy.yaml` を作成:

```yaml
language: python
style_guide: pep8
review:
  severity: medium
  include_suggestions: true
testgen:
  framework: pytest
  coverage_target: 80
output:
  format: text  # text, json, markdown
ignore_patterns:
  - "*.generated.py"
  - "migrations/*"
```

## 対応言語

| 言語 | レビュー | テスト生成 | 静的解析連携 |
|------|---------|----------|--------------|
| Python | ✅ 完全対応 | ✅ 完全対応 | flake8, mypy, pylint |
| JavaScript | ✅ 完全対応 | 🔶 部分対応 | ESLint |
| TypeScript | ✅ 完全対応 | 🔶 部分対応 | ESLint, tsc |
| Rust | ✅ 完全対応 | 🔶 部分対応 | clippy, cargo check |
| Go | ✅ 完全対応 | 🔶 部分対応 | go vet, staticcheck, golangci-lint |

## 料金プラン

| プラン | 対象 | 価格 | 機能 |
|--------|------|------|------|
| **Free** | 個人/OSS | ¥0/月 | 50レビュー/月、公開リポのみ |
| **Pro** | 個人/小規模チーム | ¥1,980/月 | 500レビュー/月、プライベートリポ対応 |
| **Team** | チーム（10名まで） | ¥9,800/月 | 無制限、GitHub連携、優先サポート |
| **Enterprise** | 大企業 | 要相談 | 自己ホスト、SSO、専任サポート |

### DevBuddyAIを選ぶ理由

- **時間削減**: コードレビュー時間を40%削減
- **早期バグ発見**: 人間が見逃すバグをAIがキャッチ
- **一貫した品質**: コーディング規約を自動的に適用
- **投資対効果**: 本番環境でのバグ1件防止で年間費用をカバー

## セキュリティとプライバシー

**あなたのコードは安全です。**

- コードはメモリ内でのみ処理 - 保存されません
- API通信はTLS 1.3で暗号化
- Enterpriseプランは自己ホスト対応 - **コードはネットワーク外に出ません**
- SOC 2 Type II準拠（Enterprise）

## CLIリファレンス

```
Usage: devbuddy [OPTIONS] COMMAND [ARGS]...

Commands:
  review    コードのバグ、スタイル問題、改善点をレビュー
  testgen   指定した関数のユニットテストを生成
  fix       失敗したテストやバグの修正を提案
  config    DevBuddyAI設定を管理
  auth      DevBuddyAIサービスで認証
  license   ライセンス管理
  billing   課金管理

Options:
  --version  バージョンを表示
  --help     ヘルプを表示

出力形式オプション:
  --format text     テキスト形式（デフォルト）
  --format json     JSON形式
  --format markdown Markdown形式

Examples:
  devbuddy review src/                    # ディレクトリ内全ファイルをレビュー
  devbuddy review --diff HEAD~1           # 変更ファイルのみレビュー
  devbuddy review src/main.py --format json  # JSON形式で出力
  devbuddy testgen src/utils.py           # ファイル全体のテストを生成
  devbuddy testgen -f calculate           # 特定関数のテストを生成
  devbuddy fix tests/test_api.py          # 失敗テストの修正を提案
```

## GitHub Action

GitHub Marketplaceで利用可能。`.github/workflows/devbuddy.yml` に追加:

### 基本的な使い方
```yaml
name: DevBuddyAI レビュー

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
      checks: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: masuda-hikari/DevBuddyAI@v1
        with:
          api_key: ${{ secrets.DEVBUDDY_API_KEY }}
```

### 詳細設定
```yaml
- uses: masuda-hikari/DevBuddyAI@v1
  with:
    api_key: ${{ secrets.DEVBUDDY_API_KEY }}
    model: 'claude-3-sonnet'        # claude-3-opus, gpt-4, gpt-3.5-turbo
    severity: 'medium'              # low, medium, high
    languages: 'auto'               # auto, python, javascript, typescript, rust, go
    review_mode: 'diff'             # diff, full
    fail_on_issues: 'false'         # true でPRをブロック
    post_comment: 'true'            # true でPRにコメント投稿
    ignore_patterns: '*.test.py'    # 無視するパターン（カンマ区切り）
```

## VSCode拡張

エディタ内で直接DevBuddyAIを使用できます。

### インストール
1. VSCode Marketplaceから「DevBuddyAI」を検索
2. または `.vsix` ファイルから直接インストール

### 機能
- **Ctrl+Shift+R**: 現在のファイルをレビュー
- **Ctrl+Shift+T**: 選択した関数のテストを生成
- **Ctrl+Shift+F**: バグ修正を提案

### 設定
```json
{
  "devbuddy.apiKey": "your-api-key",
  "devbuddy.model": "claude-3-sonnet",
  "devbuddy.severity": "medium",
  "devbuddy.autoReviewOnSave": false,
  "devbuddy.testFramework": "pytest"
}
```

## クラウドデプロイ

Webhookサーバーを本番環境にデプロイできます。

### Railway
```bash
railway login
railway up
```

### Render
リポジトリを連携すると自動デプロイ

### Fly.io
```bash
fly launch
fly deploy
```

詳細は [デプロイガイド](docs/DEPLOY_GUIDE.md) を参照してください。

## コントリビューション

コントリビューションを歓迎します！詳細は [CONTRIBUTING.md](docs/CONTRIBUTING.md) をご覧ください。

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

---

**DevBuddyAI** - AIでコード品質を向上させましょう。

[ランディングページ](https://masuda-hikari.github.io/DevBuddyAI/) | [GitHub](https://github.com/masuda-hikari/DevBuddyAI) | [サポート](mailto:support@devbuddy.ai)
