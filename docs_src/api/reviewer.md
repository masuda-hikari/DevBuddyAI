# コードレビュー (reviewer)

AIコードレビューエンジン。

## CodeReviewer

::: devbuddy.core.reviewer.CodeReviewer
    options:
      show_source: true
      members:
        - __init__
        - review_file
        - review_diff

## 使用例

### ファイルレビュー

```python
from pathlib import Path
from devbuddy.llm.client import LLMClient
from devbuddy.core.reviewer import CodeReviewer

client = LLMClient()
reviewer = CodeReviewer(client)

result = reviewer.review_file(
    Path("src/mycode.py"),
    severity="medium"
)

if result.success:
    print(f"Summary: {result.summary}")
    for issue in result.issues:
        print(f"[{issue.level}] Line {issue.line}: {issue.message}")
else:
    print(f"Error: {result.error}")
```

### diffレビュー

```python
diff_content = """
--- a/src/mycode.py
+++ b/src/mycode.py
@@ -10,6 +10,8 @@ def process_data(data):
+    result = data / 0  # 潜在的なゼロ除算
     return result
"""

result = reviewer.review_diff(diff_content)
```

## データモデル

### Issue

```python
@dataclass
class Issue:
    level: str      # "bug", "warning", "style", "info"
    line: int       # 行番号
    message: str    # メッセージ
    suggestion: Optional[str] = None  # 改善提案
```

### ReviewResult

```python
@dataclass
class ReviewResult:
    file_path: Path
    issues: list[Issue] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    summary: str = ""
```
