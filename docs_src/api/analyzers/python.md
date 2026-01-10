# Python Analyzer

Python静的解析器。AST解析、flake8、mypy連携。

## PythonAnalyzer

::: devbuddy.analyzers.python_analyzer.PythonAnalyzer
    options:
      show_source: true
      members:
        - __init__
        - analyze
        - get_functions
        - run_flake8
        - run_mypy

## 使用例

```python
from pathlib import Path
from devbuddy.analyzers.python_analyzer import PythonAnalyzer

analyzer = PythonAnalyzer()

# コード解析
code = '''
def add(a, b):
    return a + b
'''

issues = analyzer.analyze(code, Path("example.py"))
for issue in issues:
    print(f"[{issue.level}] Line {issue.line}: {issue.message}")
```

## 外部ツール連携

### flake8

```python
issues = analyzer.run_flake8(Path("src/mycode.py"))
```

### mypy

```python
issues = analyzer.run_mypy(Path("src/mycode.py"))
```

## 検出パターン

| パターン | 重要度 | 説明 |
|---------|--------|------|
| 未使用変数 | warning | 定義されたが使用されていない変数 |
| 未使用import | warning | インポートされたが使用されていないモジュール |
| 空のexcept | bug | 例外を無視している |
| print文 | style | デバッグ用print文の残留 |
| TODO/FIXME | info | 未実装・要修正のコメント |
