# インストール

## pip（推奨）

```bash
pip install devbuddy-ai
```

## ソースから

```bash
git clone https://github.com/masuda-hikari/DevBuddyAI.git
cd DevBuddyAI
pip install -e .
```

## 開発環境

```bash
git clone https://github.com/masuda-hikari/DevBuddyAI.git
cd DevBuddyAI
pip install -e ".[dev]"
```

## 環境変数

```bash
# 必須: APIキー
export DEVBUDDY_API_KEY=your_api_key_here

# オプション: モデル選択（デフォルト: claude-3-opus）
export DEVBUDDY_MODEL=claude-3-opus

# オプション: ログレベル（デフォルト: INFO）
export DEVBUDDY_LOG_LEVEL=INFO

# オプション: GitHub連携
export GITHUB_TOKEN=your_github_token
```

## 設定ファイル

プロジェクトルートに `.devbuddy.yaml` を作成:

```yaml
language: python
style_guide: pep8
review:
  severity: medium
  include_suggestions: true
testgen:
  framework: pytest
  coverage_target: 80
output:
  format: text  # text/json/markdown
ignore_patterns:
  - "*.generated.py"
  - "migrations/*"
```

## 動作確認

```bash
devbuddy --version
devbuddy --help
```
