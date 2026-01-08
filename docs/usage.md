# 使用ガイド
## 基本コマンド
### コードレビュー

```bash
# 単一ファイルをレビュー
devbuddy review src/mycode.py

# ディレクトリ全体をレビュー
devbuddy review src/

# 重要度フィルタ（low/medium/high）
devbuddy review src/mycode.py --severity high

# git diffのみレビュー
devbuddy review src/ --diff

# 結果をファイルに出力
devbuddy review src/ -o review_report.txt
```

### テスト生成
```bash
# ファイル全体のテスト生成
devbuddy testgen src/calculator.py

# 特定の関数のみ
devbuddy testgen src/calculator.py --function add

# 出力先指定
devbuddy testgen src/calculator.py -o tests/test_calculator.py

# フレームワーク指定（pytest/unittest）
devbuddy testgen src/calculator.py --framework unittest

# 生成後にテスト実行
devbuddy testgen src/calculator.py --run
```

### バグ修正提案
```bash
# 失敗テストの修正提案
devbuddy fix tests/test_api.py

# ソースファイルを指定
devbuddy fix tests/test_api.py --source src/api.py

# 修正を自動適用
devbuddy fix tests/test_api.py --apply
```

### 設定管理
```bash
# 設定ファイル初期化
devbuddy config --init

# 現在の設定表示
devbuddy config --show
```

## 設定ファイル

プロジェクトルートに`.devbuddy.yaml`を作成:

```yaml
# 対象言語
language: python

# スタイルガイド
style_guide: pep8

# レビュー設定
review:
  severity: medium          # low/medium/high
  include_suggestions: true # 改善提案を含める

# テスト生成設定
testgen:
  framework: pytest         # pytest/unittest
  coverage_target: 80       # 目標カバレッジ

# 無視パターン
ignore_patterns:
  - "*.generated.py"
  - "migrations/*"
  - "__pycache__/*"
  - ".git/*"
```

## 出力例
### コードレビュー結果

```
DevBuddyAI Code Review Results
==============================

src/calculator.py
  [BUG] Line 15: Division by zero possible when 'divisor' is 0
    Suggestion: Add guard clause: if divisor == 0: raise ValueError

  [WARNING] Line 28: Unused variable 'temp_result'
    Suggestion: Remove or use the variable

  [STYLE] Line 42: Function name 'calcResult' should use snake_case
    Suggestion: Rename to 'calc_result'

--------------------------------------------------
Summary: 1 bug, 1 warning, 1 style issue
```

### テスト生成結果

```
Generated Tests:
----------------------------------------
import pytest
from calculator import add, divide

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)

Test file saved to: tests/test_calculator.py
Running generated tests... All 4 tests passed!
```

## ベストプラクティス

### 1. 段階的なレビュー
```bash
# まず重大な問題のみ
devbuddy review src/ --severity high

# 修正後に詳細レビュー
devbuddy review src/ --severity low
```

### 2. CI/CDへの統合
```bash
# exit codeを活用
devbuddy review src/ --severity high || exit 1
```

### 3. テスト駆動開発との連携
```bash
# 1. テスト生成
devbuddy testgen src/new_feature.py -o tests/test_new_feature.py

# 2. テスト実行（失敗を確認）
pytest tests/test_new_feature.py

# 3. 実装
# 4. テスト再実行（合格を確認）
pytest tests/test_new_feature.py
```

## 高度な使用法
### GitHub Action連携

```yaml
name: DevBuddyAI Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install devbuddy-ai
      - run: devbuddy review src/ --severity high
        env:
          DEVBUDDY_API_KEY: ${{ secrets.DEVBUDDY_API_KEY }}
```

### Pre-commitフック

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: devbuddy-review
        name: DevBuddyAI Review
        entry: devbuddy review
        language: system
        types: [python]
        pass_filenames: true
```
