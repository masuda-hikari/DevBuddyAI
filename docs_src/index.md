# DevBuddyAI

**AI駆動の開発者支援ツール** - コードレビュー、テスト生成、バグ修正提案を自動化

## 概要

DevBuddyAIは最先端のAI技術を活用し、開発者の生産性を向上させるツールです。

### 主な機能

- **自動コードレビュー**: コード品質、潜在的なバグ、スタイル問題を即座にフィードバック
- **テスト自動生成**: 関数から包括的なユニットテストを自動生成
- **バグ修正提案**: 失敗テストや既知バグに対するAI駆動の修正提案
- **マルチプラットフォーム統合**: CLI、GitHub Actions、IDEプラグインで利用可能

## クイックスタート

### インストール

```bash
pip install devbuddy-ai
```

### APIキー設定

```bash
export DEVBUDDY_API_KEY=your_api_key_here
```

### コードレビュー実行

```bash
devbuddy review src/mycode.py
```

### テスト生成

```bash
devbuddy testgen src/calculator.py
```

## 対応言語

| 言語 | レビュー | テスト生成 | 静的解析 |
|------|---------|-----------|---------|
| Python | ✅ | ✅ | flake8, mypy |
| JavaScript | ✅ | 🔄 | ESLint |
| TypeScript | ✅ | 🔄 | ESLint, tsc |
| Rust | ✅ | 🔄 | clippy |
| Go | ✅ | 🔄 | go vet, staticcheck |

✅ = 完全対応, 🔄 = 部分対応

## 料金プラン

| プラン | 対象 | 価格 |
|--------|------|------|
| Free | OSS | 無料 |
| Pro | 個人 | $19/月 |
| Team | チーム | $99/月 |
| Enterprise | 企業 | お問合せ |

## リンク

- [GitHub](https://github.com/masuda-hikari/DevBuddyAI)
- [PyPI](https://pypi.org/project/devbuddy-ai/)
- [ランディングページ](https://masuda-hikari.github.io/DevBuddyAI/)
