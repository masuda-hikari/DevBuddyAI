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


class TestLLMClientComplete:
    """LLMClient.complete関連のテスト"""

    def test_complete_claude(self):
        """Claude API呼び出し"""
        import sys
        from unittest.mock import MagicMock

        mock_anthropic = MagicMock()
        mock_content = type("MockContent", (), {"text": "AI response"})()
        mock_message = type("MockMessage", (), {"content": [mock_content]})()
        mock_client = mock_anthropic.Anthropic.return_value
        mock_client.messages.create.return_value = mock_message

        sys.modules["anthropic"] = mock_anthropic

        try:
            client = LLMClient(api_key="sk-ant-test123")
            response = client.complete("test prompt")
            assert response == "AI response"
        finally:
            del sys.modules["anthropic"]

    def test_complete_claude_no_text(self):
        """Claude APIでtextがない場合"""
        import sys
        from unittest.mock import MagicMock

        mock_anthropic = MagicMock()
        mock_content = type("MockContent", (), {})()
        mock_message = type("MockMessage", (), {"content": [mock_content]})()
        mock_client = mock_anthropic.Anthropic.return_value
        mock_client.messages.create.return_value = mock_message

        sys.modules["anthropic"] = mock_anthropic

        try:
            client = LLMClient(api_key="sk-ant-test123")
            response = client.complete("test prompt")
            assert response == ""
        finally:
            del sys.modules["anthropic"]

    def test_complete_openai(self):
        """OpenAI API呼び出し"""
        import sys
        from unittest.mock import MagicMock

        mock_openai = MagicMock()
        mock_message = type("MockMessage", (), {"content": "OpenAI response"})()
        mock_choice = type("MockChoice", (), {"message": mock_message})()
        mock_response = type("MockResponse", (), {"choices": [mock_choice]})()
        mock_client = mock_openai.OpenAI.return_value
        mock_client.chat.completions.create.return_value = mock_response

        sys.modules["openai"] = mock_openai

        try:
            client = LLMClient(api_key="sk-proj-test123")
            response = client.complete("test prompt")
            assert response == "OpenAI response"
        finally:
            del sys.modules["openai"]

    def test_complete_openai_none_content(self):
        """OpenAI APIでcontentがNoneの場合"""
        import sys
        from unittest.mock import MagicMock

        mock_openai = MagicMock()
        mock_message = type("MockMessage", (), {"content": None})()
        mock_choice = type("MockChoice", (), {"message": mock_message})()
        mock_response = type("MockResponse", (), {"choices": [mock_choice]})()
        mock_client = mock_openai.OpenAI.return_value
        mock_client.chat.completions.create.return_value = mock_response

        sys.modules["openai"] = mock_openai

        try:
            client = LLMClient(api_key="sk-proj-test123")
            response = client.complete("test prompt")
            assert response == ""
        finally:
            del sys.modules["openai"]

    def test_complete_claude_import_error(self):
        """anthropicパッケージ未インストール"""
        import sys

        # anthropicモジュールを一時的に削除
        old_anthropic = sys.modules.get("anthropic")
        sys.modules["anthropic"] = None

        try:
            client = LLMClient(api_key="sk-ant-test123")
            with pytest.raises(ImportError, match="anthropic"):
                client._complete_claude("test")
        finally:
            if old_anthropic:
                sys.modules["anthropic"] = old_anthropic
            elif "anthropic" in sys.modules:
                del sys.modules["anthropic"]

    def test_complete_openai_import_error(self):
        """openaiパッケージ未インストール"""
        import sys

        old_openai = sys.modules.get("openai")
        sys.modules["openai"] = None

        try:
            client = LLMClient(api_key="sk-proj-test123")
            with pytest.raises(ImportError, match="openai"):
                client._complete_openai("test")
        finally:
            if old_openai:
                sys.modules["openai"] = old_openai
            elif "openai" in sys.modules:
                del sys.modules["openai"]


class TestLLMClientCompleteWithSystem:
    """LLMClient.complete_with_system関連のテスト"""

    def test_complete_with_system_claude(self):
        """Claude APIでシステムプロンプト付き"""
        import sys
        from unittest.mock import MagicMock

        mock_anthropic = MagicMock()
        mock_content = type("MockContent", (), {"text": "System response"})()
        mock_message = type("MockMessage", (), {"content": [mock_content]})()
        mock_client = mock_anthropic.Anthropic.return_value
        mock_client.messages.create.return_value = mock_message

        sys.modules["anthropic"] = mock_anthropic

        try:
            client = LLMClient(api_key="sk-ant-test123")
            response = client.complete_with_system("system", "user")
            assert response == "System response"
        finally:
            del sys.modules["anthropic"]

    def test_complete_with_system_claude_no_text(self):
        """Claude APIでシステムプロンプト付きtext属性なし"""
        import sys
        from unittest.mock import MagicMock

        mock_anthropic = MagicMock()
        mock_content = type("MockContent", (), {})()
        mock_message = type("MockMessage", (), {"content": [mock_content]})()
        mock_client = mock_anthropic.Anthropic.return_value
        mock_client.messages.create.return_value = mock_message

        sys.modules["anthropic"] = mock_anthropic

        try:
            client = LLMClient(api_key="sk-ant-test123")
            response = client.complete_with_system("system", "user")
            assert response == ""
        finally:
            del sys.modules["anthropic"]

    def test_complete_with_system_openai(self):
        """OpenAI APIでシステムプロンプト付き"""
        import sys
        from unittest.mock import MagicMock

        mock_openai = MagicMock()
        mock_message = type("MockMessage", (), {"content": "OpenAI sys"})()
        mock_choice = type("MockChoice", (), {"message": mock_message})()
        mock_response = type("MockResponse", (), {"choices": [mock_choice]})()
        mock_client = mock_openai.OpenAI.return_value
        mock_client.chat.completions.create.return_value = mock_response

        sys.modules["openai"] = mock_openai

        try:
            client = LLMClient(api_key="sk-proj-test123")
            response = client.complete_with_system("system", "user")
            assert response == "OpenAI sys"
        finally:
            del sys.modules["openai"]

    def test_complete_with_system_openai_none(self):
        """OpenAI APIでシステムプロンプト付きcontentがNone"""
        import sys
        from unittest.mock import MagicMock

        mock_openai = MagicMock()
        mock_message = type("MockMessage", (), {"content": None})()
        mock_choice = type("MockChoice", (), {"message": mock_message})()
        mock_response = type("MockResponse", (), {"choices": [mock_choice]})()
        mock_client = mock_openai.OpenAI.return_value
        mock_client.chat.completions.create.return_value = mock_response

        sys.modules["openai"] = mock_openai

        try:
            client = LLMClient(api_key="sk-proj-test123")
            response = client.complete_with_system("system", "user")
            assert response == ""
        finally:
            del sys.modules["openai"]

    def test_complete_with_system_claude_import_error(self):
        """anthropicパッケージ未インストール（system版）"""
        import sys

        old_anthropic = sys.modules.get("anthropic")
        sys.modules["anthropic"] = None

        try:
            client = LLMClient(api_key="sk-ant-test123")
            with pytest.raises(ImportError, match="anthropic"):
                client._complete_claude_with_system("sys", "user")
        finally:
            if old_anthropic:
                sys.modules["anthropic"] = old_anthropic
            elif "anthropic" in sys.modules:
                del sys.modules["anthropic"]

    def test_complete_with_system_openai_import_error(self):
        """openaiパッケージ未インストール（system版）"""
        import sys

        old_openai = sys.modules.get("openai")
        sys.modules["openai"] = None

        try:
            client = LLMClient(api_key="sk-proj-test123")
            with pytest.raises(ImportError, match="openai"):
                client._complete_openai_with_system("sys", "user")
        finally:
            if old_openai:
                sys.modules["openai"] = old_openai
            elif "openai" in sys.modules:
                del sys.modules["openai"]
