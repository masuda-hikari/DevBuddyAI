# API リファレンス

## コアモジュール

### CodeReviewer

コードレビューエンジン。

```python
from devbuddy.core.reviewer import CodeReviewer
from devbuddy.llm.client import LLMClient

client = LLMClient(api_key="your_key")
reviewer = CodeReviewer(client=client)

# ファイルをレビュー
result = reviewer.review_file(
    file_path=Path("src/mycode.py"),
    severity="medium"  # low/medium/high
)

print(f"Success: {result.success}")
for issue in result.issues:
    print(f"[{issue.level}] Line {issue.line}: {issue.message}")
```

#### ReviewResult

| 属性 | 型 | 説明 |
|------|-----|------|
| file_path | Path | レビュー対象ファイル |
| issues | list[Issue] | 検出された問題リスト |
| summary | str | サマリー文字列 |
| success | bool | 成功フラグ |
| error | str | エラーメッセージ |

#### Issue

| 属性 | 型 | 説明 |
|------|-----|------|
| level | str | レベル（bug/warning/style/info） |
| line | int | 行番号 |
| message | str | メッセージ |
| suggestion | str | 改善提案 |

### TestGenerator

テスト生成エンジン。

```python
from devbuddy.core.generator import TestGenerator
from devbuddy.llm.client import LLMClient

client = LLMClient(api_key="your_key")
generator = TestGenerator(client=client)

# テスト生成
result = generator.generate_tests(
    source_path=Path("src/calculator.py"),
    function_name="add",  # None で全関数
    framework="pytest"    # pytest/unittest
)

if result.success:
    print(result.test_code)
    print(f"Generated {result.test_count} tests")

# 生成＆検証（自己検証ループ）
result = generator.generate_and_verify(
    source_path=Path("src/calculator.py"),
    framework="pytest"
)
print(f"Verified: {result.verified}")
```

#### GenerationResult

| 属性 | 型 | 説明 |
|------|-----|------|
| success | bool | 成功フラグ |
| test_code | str | 生成されたテストコード |
| error | str | エラーメッセージ |
| test_count | int | 生成テスト数 |
| verified | bool | 検証済みフラグ |

### BugFixer

バグ修正エンジン。

```python
from devbuddy.core.fixer import BugFixer
from devbuddy.llm.client import LLMClient

client = LLMClient(api_key="your_key")
fixer = BugFixer(client=client)

# 修正提案
result = fixer.suggest_fix(
    test_path=Path("tests/test_api.py"),
    source_path=Path("src/api.py")  # オプション
)

for suggestion in result.suggestions:
    print(f"File: {suggestion.file_path}:{suggestion.line}")
    print(f"Description: {suggestion.description}")
    print(f"- {suggestion.original}")
    print(f"+ {suggestion.replacement}")

# 修正適用
for suggestion in result.suggestions:
    success = fixer.apply_fix(suggestion)
```

## LLMモジュール

### LLMClient

LLM APIクライアント。Claude/OpenAI両対応。

```python
from devbuddy.llm.client import LLMClient

# 環境変数から自動設定
client = LLMClient()

# 明示的に指定
client = LLMClient(
    api_key="your_key",
    model="claude-3-opus-20240229"
)

# 補完
response = client.complete("Review this code: ...")

# システムプロンプト付き
response = client.complete_with_system(
    system_prompt="You are a code reviewer.",
    user_prompt="Review this: ..."
)
```

### MockLLMClient

テスト用モッククライアント。

```python
from devbuddy.llm.client import MockLLMClient

mock = MockLLMClient(responses={
    "review": "[WARNING] Line 10: Issue found",
    "test": "def test_example(): pass"
})

# キーワードにマッチするレスポンスを返す
response = mock.complete("Please review this code")
# -> "[WARNING] Line 10: Issue found"
```

## Analyzerモジュール

### PythonAnalyzer

Python静的解析エンジン。

```python
from devbuddy.analyzers.python_analyzer import PythonAnalyzer, AnalysisConfig

# カスタム設定
config = AnalysisConfig(
    use_flake8=True,
    use_mypy=True,
    max_line_length=100,
    ignore_codes=["E501"]
)

analyzer = PythonAnalyzer(config=config)

# コード解析
issues = analyzer.analyze(
    code="def f(): pass",
    file_path=Path("src/code.py")  # 外部ツール用
)

# 構文チェック
valid, error = analyzer.check_syntax("x = 1 +")

# 関数/クラス取得
functions = analyzer.get_functions(code)
classes = analyzer.get_classes(code)
```

## Integrationモジュール

### GitHubIntegration

GitHub連携。

```python
from devbuddy.integrations.github import GitHubIntegration, PRComment

github = GitHubIntegration(token="your_token")

# PRのdiff取得
diff = github.get_pr_diff("owner/repo", pr_number=123)

# コメント投稿
github.post_review_comment(
    repo_name="owner/repo",
    pr_number=123,
    comment=PRComment(
        body="Please fix this issue",
        path="src/code.py",
        line=42
    )
)
```

### GitOperations

ローカルGit操作。

```python
from devbuddy.integrations.git import GitOperations

git = GitOperations(repo_path=Path("."))

# diff取得
diff_info = git.get_diff(staged=True)
print(f"Files changed: {diff_info.files_changed}")

# 変更ファイルリスト
files = git.get_changed_files()

# コミット情報
commit = git.get_commit_info("HEAD")
print(f"Author: {commit.author}")
```
