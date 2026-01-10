"""
LLMClientのテスト
"""

import pytest
from unittest.mock import patch

from devbuddy.llm.client import (
    LLMClient,
    LLMConfig,
    MockLLMClient,
    BaseLLMClient,
)


class TestLLMConfig:
    """LLMConfigテストクラス"""

    def test_default_config(self):
        """デフォルト設定"""
        config = LLMConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.model == "claude-3-opus-20240229"
        assert config.max_tokens == 4096
        assert config.temperature == 0.3
        assert config.timeout == 60

    def test_custom_config(self):
        """カスタム設定"""
        config = LLMConfig(
            api_key="custom-key",
            model="gpt-4",
            max_tokens=2048,
            temperature=0.7,
            timeout=120,
        )

        assert config.api_key == "custom-key"
        assert config.model == "gpt-4"
        assert config.max_tokens == 2048
        assert config.temperature == 0.7


class TestLLMClient:
    """LLMClientテストクラス"""

    def test_init_with_api_key(self):
        """APIキー指定での初期化"""
        client = LLMClient(api_key="test-api-key")

        assert client.api_key == "test-api-key"
        assert client.config.api_key == "test-api-key"

    def test_init_no_api_key_raises(self):
        """APIキーなしでエラー"""
        with patch.dict("os.environ", {"DEVBUDDY_API_KEY": ""}):
            with pytest.raises(ValueError, match="API key is required"):
                LLMClient(api_key="")

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "env-api-key"})
    def test_init_from_env(self):
        """環境変数からAPIキー取得"""
        client = LLMClient()

        assert client.api_key == "env-api-key"

    @patch.dict("os.environ", {"DEVBUDDY_MODEL": "custom-model"})
    def test_model_from_env(self):
        """環境変数からモデル取得"""
        client = LLMClient(api_key="test-key")

        assert client.model == "custom-model"

    def test_detect_api_type_claude(self):
        """Claude APIキー判定"""
        client = LLMClient(api_key="sk-ant-api123456")

        assert client._api_type == "claude"

    def test_detect_api_type_openai(self):
        """OpenAI APIキー判定"""
        client = LLMClient(api_key="sk-proj-api123456")

        assert client._api_type == "openai"

    def test_detect_api_type_default(self):
        """不明なキー形式はClaude"""
        client = LLMClient(api_key="unknown-format-key")

        assert client._api_type == "claude"


class TestMockLLMClient:
    """MockLLMClientテストクラス"""

    def test_default_response(self):
        """デフォルトレスポンス"""
        client = MockLLMClient()

        response = client.complete("any prompt")

        assert "[INFO]" in response
        assert "Code looks good" in response

    def test_keyword_response(self):
        """キーワードマッチレスポンス"""
        client = MockLLMClient(responses={
            "review": "Review response",
            "test": "Test response",
        })

        assert client.complete("please review this") == "Review response"
        assert client.complete("generate test") == "Test response"

    def test_call_history(self):
        """呼び出し履歴"""
        client = MockLLMClient()

        client.complete("prompt 1")
        client.complete("prompt 2")

        assert len(client.call_history) == 2
        assert "prompt 1" in client.call_history
        assert "prompt 2" in client.call_history

    def test_set_response(self):
        """レスポンス設定"""
        client = MockLLMClient()

        client.set_response("custom", "custom response")
        response = client.complete("custom keyword")

        assert response == "custom response"

    def test_is_base_client(self):
        """BaseLLMClient継承"""
        client = MockLLMClient()

        assert isinstance(client, BaseLLMClient)
