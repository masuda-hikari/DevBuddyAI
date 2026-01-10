# Rust Analyzer

Rust静的解析器。clippy、cargo check連携。

## RustAnalyzer

::: devbuddy.analyzers.rust_analyzer.RustAnalyzer
    options:
      show_source: true
      members:
        - __init__
        - analyze
        - run_clippy
        - run_cargo_check

## 使用例

```python
from pathlib import Path
from devbuddy.analyzers.rust_analyzer import RustAnalyzer

analyzer = RustAnalyzer()

# コード解析
code = '''
fn main() {
    let result = some_option.unwrap();
    println!("{}", result);
}
'''

issues = analyzer.analyze(code, Path("example.rs"))
for issue in issues:
    print(f"[{issue.level}] Line {issue.line}: {issue.message}")
```

## 外部ツール連携

### Clippy

```python
issues = analyzer.run_clippy(Path("src/main.rs"))
```

### Cargo Check

```python
issues = analyzer.run_cargo_check(Path("src/lib.rs"))
```

## 検出パターン

| パターン | 重要度 | 説明 |
|---------|--------|------|
| unwrap() | warning | パニックの可能性 |
| expect("") | warning | 空のexpectメッセージ |
| panic! | warning | 明示的なパニック |
| println!/dbg! | style | デバッグ用出力の残留 |
| unsafe | warning | unsafeブロック |
| transmute | bug | 危険な型変換 |
| TODO/FIXME | info | 未実装・要修正のコメント |
| clone()連発 | style | 過剰なclone使用 |
