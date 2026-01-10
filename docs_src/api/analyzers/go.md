# Go Analyzer

Go静的解析器。go vet、staticcheck、golangci-lint連携。

## GoAnalyzer

::: devbuddy.analyzers.go_analyzer.GoAnalyzer
    options:
      show_source: true
      members:
        - __init__
        - analyze
        - run_go_vet
        - run_staticcheck
        - run_golangci_lint

## 使用例

```python
from pathlib import Path
from devbuddy.analyzers.go_analyzer import GoAnalyzer

analyzer = GoAnalyzer()

# コード解析
code = '''
package main

import "fmt"

func main() {
    result, _ := someFunction()  // エラー無視
    fmt.Println(result)
}
'''

issues = analyzer.analyze(code, Path("example.go"))
for issue in issues:
    print(f"[{issue.level}] Line {issue.line}: {issue.message}")
```

## 外部ツール連携

### go vet

```python
issues = analyzer.run_go_vet(Path("main.go"))
```

### staticcheck

```python
issues = analyzer.run_staticcheck(Path("main.go"))
```

### golangci-lint

```python
issues = analyzer.run_golangci_lint(Path("main.go"))
```

## 検出パターン

| パターン | 重要度 | 説明 |
|---------|--------|------|
| panic() | warning | パニックの可能性 |
| recover() | warning | 不適切なrecover使用 |
| fmt.Print* | style | デバッグ用出力の残留 |
| エラー無視 `_, _` | bug | エラーハンドリングの欠如 |
| unsafe | warning | unsafeパッケージ使用 |
| reflect | warning | reflectパッケージ使用 |
| TODO/FIXME | info | 未実装・要修正のコメント |
