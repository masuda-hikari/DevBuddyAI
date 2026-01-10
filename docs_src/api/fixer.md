# バグ修正 (fixer)

AIバグ修正提案エンジン。

## BugFixer

::: devbuddy.core.fixer.BugFixer
    options:
      show_source: true
      members:
        - __init__
        - suggest_fix

## 使用例

### 失敗テストの修正提案

```python
from pathlib import Path
from devbuddy.llm.client import LLMClient
from devbuddy.core.fixer import BugFixer

client = LLMClient()
fixer = BugFixer(client)

result = fixer.suggest_fix(
    Path("tests/test_api.py"),
    error_output="AssertionError: expected 5, got 4"
)

if result.success:
    print("Suggested fix:")
    print(result.suggested_fix)
else:
    print(f"Error: {result.error}")
```

### エラー出力から修正提案

```python
error_output = """
FAILED tests/test_calculator.py::test_divide
AssertionError: ZeroDivisionError not raised
"""

result = fixer.suggest_fix(
    Path("src/calculator.py"),
    error_output=error_output
)
```

## データモデル

### FixResult

```python
@dataclass
class FixResult:
    success: bool                 # 修正提案成功
    suggested_fix: str = ""       # 提案された修正コード
    explanation: str = ""         # 修正の説明
    error: Optional[str] = None   # エラーメッセージ
```
