# LLMクライアント (client)

LLM APIクライアント。Claude/OpenAI両対応。

## LLMClient

::: devbuddy.llm.client.LLMClient
    options:
      show_source: true
      members:
        - __init__
        - complete
        - complete_stream

## 使用例

### 基本的な使い方

```python
from devbuddy.llm.client import LLMClient

# 環境変数から自動設定
client = LLMClient()

# レスポンス取得
response = client.complete("Pythonでfizzbuzzを実装してください")
print(response)
```

### モデル指定

```python
# Claude使用
client = LLMClient(
    api_key="your_api_key",
    model="claude-3-opus"
)

# OpenAI使用
client = LLMClient(
    api_key="your_api_key",
    model="gpt-4"
)
```

### ストリーミング

```python
for chunk in client.complete_stream("長い説明をお願いします"):
    print(chunk, end="", flush=True)
```

## 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| DEVBUDDY_API_KEY | APIキー | - |
| DEVBUDDY_MODEL | モデル名 | claude-3-opus |
| DEVBUDDY_MAX_TOKENS | 最大トークン数 | 4096 |
| DEVBUDDY_TEMPERATURE | 温度 | 0.0 |

## 対応モデル

### Claude (Anthropic)

- claude-3-opus
- claude-3-sonnet
- claude-3-haiku

### OpenAI

- gpt-4
- gpt-4-turbo
- gpt-3.5-turbo
