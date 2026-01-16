# 🚀 クイックスタート（5分で始める）

DevBuddyAIを今すぐ試してみましょう。わずか5分でAIによるコードレビュー・テスト生成を体験できます。

## ステップ1: インストール（30秒）

```bash
pip install devbuddy-ai
```

## ステップ2: APIキー設定（1分）

### Claude API（推奨）

1. [Anthropic Console](https://console.anthropic.com/)でAPIキーを取得
2. 環境変数に設定：

```bash
# Linux/Mac
export DEVBUDDY_API_KEY=sk-ant-api03-...

# Windows (PowerShell)
$env:DEVBUDDY_API_KEY="sk-ant-api03-..."

# Windows (CMD)
set DEVBUDDY_API_KEY=sk-ant-api03-...
```

### OpenAI API

```bash
export DEVBUDDY_API_KEY=sk-...
export DEVBUDDY_MODEL=gpt-4
```

## ステップ3: サンプルコードで試す（3分）

### 3-1. サンプルコードをダウンロード

```bash
# GitHub リポジトリからサンプル取得
git clone https://github.com/masuda-hikari/DevBuddyAI.git
cd DevBuddyAI/samples
```

または、以下のコードを `sample.py` として保存：

```python
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total / len(numbers)

def find_max(data):
    max = data[0]
    for item in data:
        if item > max:
            max = item
    return max
```

### 3-2. コードレビュー

```bash
devbuddy review sample.py
```

**出力例：**
```
DevBuddyAI Code Review Results:
================================

[WARNING] Line 6: Division by zero possible when numbers is empty
  Suggestion: Add guard clause: if not numbers: return 0

[STYLE] Line 10: Built-in name 'max' used as variable
  Suggestion: Use different variable name like 'maximum'

[INFO] Line 2: Consider using built-in sum() function
  Suggestion: total = sum(numbers)

Summary: 0 bugs, 1 warning, 2 style issues found
Quality Score: 75/100
```

### 3-3. テスト自動生成

```bash
devbuddy testgen sample.py
```

**出力例：**
```
Generated test file: tests/test_sample.py

def test_calculate_average_normal():
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0

def test_calculate_average_empty():
    # Edge case: empty list should handle gracefully
    with pytest.raises(ZeroDivisionError):
        calculate_average([])

def test_find_max_positive():
    assert find_max([1, 5, 3, 9, 2]) == 9

def test_find_max_negative():
    assert find_max([-5, -1, -10]) == -1

Running generated tests...
✓ test_calculate_average_normal PASSED
✗ test_calculate_average_empty FAILED
✓ test_find_max_positive PASSED
✓ test_find_max_negative PASSED

3/4 tests passed (75%)
```

### 3-4. バグ修正提案

```bash
devbuddy fix sample.py
```

**出力例：**
```
DevBuddyAI Bug Fix Suggestions:
================================

Issue #1: Division by zero in calculate_average()
Severity: HIGH
Confidence: 95%

Suggested Fix:
---
def calculate_average(numbers):
    if not numbers:
        return 0  # または raise ValueError("Empty list")
    total = 0
    for n in numbers:
        total = total + n
    return total / len(numbers)
---

Issue #2: Variable name 'max' shadows built-in
Severity: LOW
Confidence: 100%

Suggested Fix:
---
def find_max(data):
    maximum = data[0]  # 'max' → 'maximum'
    for item in data:
        if item > maximum:
            maximum = item
    return maximum
---

Apply fixes? [y/N]: y
✓ Fixes applied to sample.py
✓ All tests now pass!
```

## 次のステップ

### より詳しい使い方

- [使い方ガイド](usage.md): 全機能の詳細説明
- [設定ファイル](.devbuddy.yaml): プロジェクト設定のカスタマイズ
- [API リファレンス](api.md): プログラムからの利用

### 実践的なサンプル

DevBuddyAIは以下のようなコードでも効果的です：

- [Web APIサーバー](../samples/web_api_server.py): FastAPI/Flask
- [CLIツール](../samples/cli_tool.py): argparse/click
- [データ処理](../samples/data_processing.py): pandas/numpy

```bash
# これらのサンプルでも試してみましょう
devbuddy review samples/web_api_server.py
devbuddy testgen samples/cli_tool.py
```

### GitHub連携（チーム向け）

プルリクエストで自動レビュー：

```yaml
# .github/workflows/devbuddy.yml
name: DevBuddyAI Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: masuda-hikari/DevBuddyAI@v1
        with:
          api_key: ${{ secrets.DEVBUDDY_API_KEY }}
```

詳細: [GitHub Action](../README.md#github-action-marketplace)

## 有料プランでさらに強力に

無料プランでは月50回までレビュー可能ですが、より多くのプロジェクトで使いたい場合：

| プラン | 価格 | レビュー回数 |
|--------|------|--------------|
| **Free** | ¥0/月 | 50回/月 |
| **Pro** | ¥1,980/月 | 500回/月 + プライベートリポジトリ |
| **Team** | ¥9,800/月 | 無制限 + GitHub連携 |

```bash
# プラン確認
devbuddy billing plans

# アップグレード
devbuddy billing upgrade pro
```

## トラブルシューティング

### APIキーが認識されない

```bash
# 設定確認
echo $DEVBUDDY_API_KEY  # Linux/Mac
echo %DEVBUDDY_API_KEY%  # Windows

# または .devbuddy.yaml に直接記載（非推奨）
api_key: sk-ant-api03-...
```

### レビュー結果が返ってこない

- ネットワーク接続を確認
- APIキーの有効期限を確認
- `--verbose` オプションで詳細ログを確認：

```bash
devbuddy review sample.py --verbose
```

### もっと詳しいレビューが欲しい

重要度レベルを調整：

```bash
devbuddy review sample.py --severity low  # 細かい指摘も含む
```

## フィードバック・サポート

- 🐛 バグ報告: [GitHub Issues](https://github.com/masuda-hikari/DevBuddyAI/issues)
- 💬 質問・相談: [Discussions](https://github.com/masuda-hikari/DevBuddyAI/discussions)
- 📧 メール: support@devbuddy.ai

---

**さあ、AIペアプログラマーとの開発を始めましょう！** 🚀
