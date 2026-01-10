# JavaScript/TypeScript Analyzer

JavaScript/TypeScript静的解析器。ESLint、tsc連携。

## JavaScriptAnalyzer

::: devbuddy.analyzers.js_analyzer.JavaScriptAnalyzer
    options:
      show_source: true
      members:
        - __init__
        - analyze
        - run_eslint
        - run_tsc

## 使用例

```python
from pathlib import Path
from devbuddy.analyzers.js_analyzer import JavaScriptAnalyzer

analyzer = JavaScriptAnalyzer()

# コード解析
code = '''
function add(a, b) {
    console.log(a + b);
    return a + b;
}
'''

issues = analyzer.analyze(code, Path("example.js"))
for issue in issues:
    print(f"[{issue.level}] Line {issue.line}: {issue.message}")
```

## 外部ツール連携

### ESLint

```python
issues = analyzer.run_eslint(Path("src/app.js"))
```

### TypeScript Compiler (tsc)

```python
issues = analyzer.run_tsc(Path("src/app.ts"))
```

## 検出パターン

| パターン | 重要度 | 説明 |
|---------|--------|------|
| console.log | style | デバッグ用コンソール出力 |
| debugger | warning | デバッガー文の残留 |
| var使用 | warning | let/constを推奨 |
| ==使用 | warning | ===を推奨 |
| eval使用 | bug | セキュリティリスク |
| TODO/FIXME | info | 未実装・要修正のコメント |
