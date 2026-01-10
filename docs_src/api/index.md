# APIリファレンス

DevBuddyAIのPython APIドキュメント。

## モジュール構成

```
devbuddy/
├── core/           # コアエンジン
│   ├── reviewer    # コードレビュー
│   ├── generator   # テスト生成
│   ├── fixer       # バグ修正
│   └── formatters  # 出力フォーマット
├── analyzers/      # 静的解析
│   ├── python      # Python解析
│   ├── js          # JS/TS解析
│   ├── rust        # Rust解析
│   └── go          # Go解析
├── llm/            # LLM連携
│   ├── client      # APIクライアント
│   └── prompts     # プロンプト
└── integrations/   # 外部連携
    ├── github      # GitHub連携
    └── git         # Git操作
```

## 基本的な使い方

```python
from devbuddy.llm.client import LLMClient
from devbuddy.core.reviewer import CodeReviewer

# クライアント初期化
client = LLMClient()

# レビュー実行
reviewer = CodeReviewer(client)
result = reviewer.review_file(Path("src/mycode.py"))

for issue in result.issues:
    print(f"[{issue.level}] Line {issue.line}: {issue.message}")
```

## テスト生成

```python
from devbuddy.core.generator import CodeTestGenerator

generator = CodeTestGenerator(client)
result = generator.generate_tests(Path("src/calculator.py"))

print(result.test_code)
```

## バグ修正提案

```python
from devbuddy.core.fixer import BugFixer

fixer = BugFixer(client)
result = fixer.suggest_fix(Path("tests/test_api.py"))

print(result.suggested_fix)
```
