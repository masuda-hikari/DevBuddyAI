# 出力フォーマット (formatters)

出力フォーマッター。Text/JSON/Markdown形式に対応。

## OutputFormatter

::: devbuddy.core.formatters.OutputFormatter
    options:
      show_source: true

## TextFormatter

::: devbuddy.core.formatters.TextFormatter
    options:
      show_source: true

## JSONFormatter

::: devbuddy.core.formatters.JSONFormatter
    options:
      show_source: true

## MarkdownFormatter

::: devbuddy.core.formatters.MarkdownFormatter
    options:
      show_source: true

## get_formatter

::: devbuddy.core.formatters.get_formatter
    options:
      show_source: true

## 使用例

### 基本的な使い方

```python
from devbuddy.core.formatters import get_formatter

# フォーマッター取得
formatter = get_formatter("json")

# レビュー結果をフォーマット
output = formatter.format_review(result)
print(output)
```

### Text形式

```python
formatter = get_formatter("text")
print(formatter.format_review(result))
```

出力例:
```
DevBuddyAI Code Review Results:
================================

[WARNING] Line 23: 潜在的なNull参照
  提案: nullチェックを追加

Summary: 1 warning found
```

### JSON形式

```python
formatter = get_formatter("json")
print(formatter.format_review(result))
```

出力例:
```json
{
  "file_path": "src/mycode.py",
  "success": true,
  "issues": [
    {
      "level": "warning",
      "line": 23,
      "message": "潜在的なNull参照",
      "suggestion": "nullチェックを追加"
    }
  ],
  "summary": "1 warning found"
}
```

### Markdown形式

```python
formatter = get_formatter("markdown")
print(formatter.format_review(result))
```

出力例:
```markdown
# DevBuddyAI Code Review

**File**: `src/mycode.py`

## Issues

| Level | Line | Message |
|-------|------|---------|
| ⚠️ warning | 23 | 潜在的なNull参照 |

## Summary
1 warning found
```
