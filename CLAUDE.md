# 🤖 DevBuddyAI - AI駆動開発アシスタント

継承: O:\Dev\CLAUDE.md → このファイル

## 📋 プロジェクト概要

**DevBuddyAI**はAIを活用した開発者支援ツール。コードレビュー、テスト生成、バグ修正提案を自動化し、開発効率を大幅に向上させる。

### ビジョン
- 開発者の「AIペアプログラマー」として機能
- コード品質向上とレビュー時間削減を両立
- 企業の開発プロセスに統合可能な柔軟性

---

## 🎯 コア機能

### 1. AIコードレビュー
- コード変更（diff/ファイル）をAIが分析
- バグ、スタイル問題、ドキュメント不足を指摘
- 改善提案を具体的なコード例で提示

### 2. テスト自動生成
- 関数/クラスからユニットテストを自動生成
- エッジケース、境界値テストを考慮
- pytest/unittest形式で出力

### 3. バグ修正提案
- 失敗テストや既知バグに対する修正案を提示
- 修正コードを自動生成し検証可能

### 4. 統合オプション
- **CLI**: `devbuddy review <file>` / `devbuddy testgen <file>`
- **GitHub Action/Bot**: PR自動コメント
- **IDE Plugin**: 将来対応予定

---

## 🔧 技術設計

### アーキテクチャ
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   CLI/API   │────▶│  Core Engine │────▶│  LLM API    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │ Analyzer │  │ Generator│
              └──────────┘  └──────────┘
```

### 技術スタック
| コンポーネント | 技術 |
|---------------|------|
| 言語 | Python 3.12+ |
| CLI | Click |
| LLM API | Claude API / OpenAI API |
| 静的解析 | ast, flake8, pylint |
| テスト | pytest |
| GitHub連携 | PyGithub |

### ディレクトリ構造
```
DevBuddyAI/
├── src/devbuddy/         # メインパッケージ
│   ├── __init__.py
│   ├── cli.py            # CLIエントリポイント
│   ├── core/
│   │   ├── reviewer.py   # コードレビューエンジン
│   │   ├── generator.py  # テスト生成エンジン
│   │   └── fixer.py      # バグ修正エンジン
│   ├── llm/
│   │   ├── client.py     # LLM APIクライアント
│   │   └── prompts.py    # プロンプトテンプレート
│   ├── analyzers/
│   │   ├── python_analyzer.py
│   │   └── js_analyzer.py
│   └── integrations/
│       ├── github.py     # GitHub連携
│       └── git.py        # Git操作
├── samples/              # サンプルコード
├── tests/                # テストコード
├── docs/                 # ドキュメント
└── .github/workflows/    # GitHub Actions
```

---

## 🔄 処理フロー

### コードレビュー
1. ファイル/diffを読み込み
2. 言語を検出し適切なAnalyzerを選択
3. 静的解析を実行（flake8等）
4. コードをLLMに送信（プロンプト付き）
5. レスポンスを解析しフォーマット
6. 結果を出力（CLI/GitHub Comment）

### テスト生成
1. 対象ファイル/関数を解析
2. 関数シグネチャ、docstring、型ヒントを抽出
3. LLMにテスト生成を依頼
4. 生成テストを実行し検証
5. 失敗時は修正を試行（最大3回）

### 自己検証ループ
```
生成 → 実行 → 失敗? → 修正 → 再実行
         ↓              ↑
       成功 ←──────────┘
```

---

## 📊 対応言語

### Phase 1（初期）
- **Python**: ast解析 + flake8 + mypy

### Phase 2（拡張）
- **JavaScript/TypeScript**: ESLint連携
- **Rust**: clippy連携
- **Go**: go vet連携

---

## 🔐 セキュリティ考慮

### APIキー管理
- 環境変数経由のみ（`DEVBUDDY_API_KEY`）
- ハードコード絶対禁止
- `.env`ファイル対応（gitignore必須）

### コードプライバシー
- ローカル処理オプション提供
- エンタープライズ向け自己ホスト版
- 送信前にユーザー確認オプション

### データ保護
- コードはAPIコール後に保持しない
- ログにコード内容を含めない設計

---

## 💰 マネタイズ戦略

### 価格モデル
| プラン | 対象 | 価格 |
|--------|------|------|
| Free | OSS（公開リポジトリ） | 無料 |
| Pro | 個人/小規模チーム | $19/月 |
| Team | 中規模チーム（10名まで） | $99/月 |
| Enterprise | 大企業・自己ホスト | 要問合せ |

### 機能制限
| 機能 | Free | Pro | Team | Enterprise |
|------|------|-----|------|------------|
| レビュー回数/月 | 50 | 500 | 無制限 | 無制限 |
| ファイルサイズ | 500行 | 2000行 | 無制限 | 無制限 |
| プライベートリポ | ✗ | ✓ | ✓ | ✓ |
| GitHub連携 | ✗ | ✓ | ✓ | ✓ |
| 自己ホスト | ✗ | ✗ | ✗ | ✓ |
| 優先サポート | ✗ | ✗ | ✓ | ✓ |

### 差別化要因
- 自己検証ループによる高精度提案
- エンタープライズ向けオンプレ対応
- 複数言語対応の柔軟性

---

## 📝 開発計画

### Phase 1: 基盤構築
- [x] プロジェクト構造作成
- [ ] CLI基本構造（click）
- [ ] LLMクライアント実装
- [ ] プロンプトテンプレート設計

### Phase 2: コアエンジン
- [ ] Pythonコードレビュー機能
- [ ] テスト生成機能
- [ ] 自己検証ループ実装

### Phase 3: 統合
- [ ] GitHub Action対応
- [ ] PR自動コメント機能
- [ ] 設定ファイル対応

### Phase 4: 拡張
- [ ] 追加言語対応
- [ ] バグ修正提案機能
- [ ] ライセンス/認証システム

---

## ⚙️ 設定

### 環境変数
```bash
DEVBUDDY_API_KEY=<claude/openai api key>
DEVBUDDY_MODEL=claude-3-opus  # または gpt-4
DEVBUDDY_LOG_LEVEL=INFO
GITHUB_TOKEN=<optional for github integration>
```

### 設定ファイル（.devbuddy.yaml）
```yaml
language: python
style_guide: pep8
max_file_size: 2000
ignore_patterns:
  - "*.generated.py"
  - "migrations/*"
review:
  severity: medium  # low/medium/high
  include_suggestions: true
testgen:
  framework: pytest
  coverage_target: 80
```

---

## 🚫 禁止事項

- APIキーのハードコード
- ユーザーコードのログ出力
- 無断での外部API送信
- テスト未実行でのリリース

---

## ✅ 品質基準

- ユニットテストカバレッジ: 80%+
- 型ヒント: 全public関数
- ドキュメント: 全public API
- 静的解析: flake8/mypy通過必須
