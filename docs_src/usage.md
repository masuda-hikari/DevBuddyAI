# 使い方

## コードレビュー

### 基本

```bash
devbuddy review src/mycode.py
```

### オプション

```bash
# 重要度フィルタ
devbuddy review src/ --severity high

# 出力形式指定
devbuddy review src/mycode.py --format json
devbuddy review src/mycode.py --format markdown

# diffレビュー
devbuddy review --diff HEAD~1
```

### 出力例

```
DevBuddyAI Code Review Results:
================================

[WARNING] Line 23: 潜在的なNull参照 - 'data' がNoneの可能性
  提案: data.items()アクセス前にnullチェックを追加

[STYLE] Line 45: 関数 'processData' はsnake_caseを使用すべき
  提案: 'process_data' にリネーム

[BUG] Line 67: count == 0 の場合にゼロ除算の可能性
  提案: ガード句を追加: if count == 0: return 0

Summary: 1 bug, 1 warning, 1 style issue found
```

## テスト生成

### 基本

```bash
devbuddy testgen src/calculator.py
```

### オプション

```bash
# 特定関数のみ
devbuddy testgen src/calculator.py --function add

# フレームワーク指定
devbuddy testgen src/calculator.py --framework unittest

# 出力形式指定
devbuddy testgen src/calculator.py --format json
```

### 出力例

```python
def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 5) == 5
```

## バグ修正提案

### 基本

```bash
devbuddy fix tests/test_api.py
```

### オプション

```bash
# 出力形式指定
devbuddy fix tests/test_api.py --format markdown
```

## 設定管理

### 設定ファイル初期化

```bash
devbuddy config --init
```

### 設定値取得

```bash
devbuddy config --get review.severity
```

### 設定値変更

```bash
devbuddy config --set review.severity=high
```

### 利用可能キー一覧

```bash
devbuddy config --list-keys
```

## GitHub Action連携

`.github/workflows/devbuddy.yml` を作成:

```yaml
name: DevBuddyAI Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: devbuddy/action@v1
        with:
          api_key: ${{ secrets.DEVBUDDY_API_KEY }}
          review_mode: "diff"
```
