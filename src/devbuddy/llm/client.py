"""
LLMClient - LLM APIクライアント

Claude/OpenAI APIとの通信を担当。
"""

import os
from dataclasses import dataclass
from typing import Optional
from abc import ABC, abstractmethod


@dataclass
class LLMConfig:
    """LLM設定"""

    api_key: str
    model: str = "claude-3-opus-20240229"
    max_tokens: int = 4096
    temperature: float = 0.3
    timeout: int = 60


class BaseLLMClient(ABC):
    """LLMクライアント基底クラス"""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """プロンプトを送信してレスポンスを取得"""
        pass


class LLMClient(BaseLLMClient):
    """LLM APIクライアント

    Claude APIまたはOpenAI APIをサポート。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("DEVBUDDY_API_KEY", "")
        self.model = model or os.environ.get("DEVBUDDY_MODEL", "claude-3-opus-20240229")

        if not self.api_key:
            raise ValueError("API key is required")

        self.config = LLMConfig(
            api_key=self.api_key,
            model=self.model,
        )

        # APIタイプを判定
        self._api_type = self._detect_api_type()

    def _detect_api_type(self) -> str:
        """APIキーからAPIタイプを判定"""
        if self.api_key.startswith("sk-ant-"):
            return "claude"
        elif self.api_key.startswith("sk-"):
            return "openai"
        else:
            # デフォルトはClaudeとして扱う
            return "claude"

    def complete(self, prompt: str) -> str:
        """プロンプトを送信してレスポンスを取得

        Args:
            prompt: プロンプト文字列

        Returns:
            str: AIのレスポンス
        """
        if self._api_type == "claude":
            return self._complete_claude(prompt)
        else:
            return self._complete_openai(prompt)

    def _complete_claude(self, prompt: str) -> str:
        """Claude APIを呼び出し"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        message = client.messages.create(
            model=self.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return message.content[0].text

    def _complete_openai(self, prompt: str) -> str:
        """OpenAI APIを呼び出し"""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")

        client = openai.OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model=self.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.choices[0].message.content or ""

    def complete_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """システムプロンプト付きで呼び出し

        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザープロンプト

        Returns:
            str: AIのレスポンス
        """
        if self._api_type == "claude":
            return self._complete_claude_with_system(system_prompt, user_prompt)
        else:
            return self._complete_openai_with_system(system_prompt, user_prompt)

    def _complete_claude_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Claude APIをシステムプロンプト付きで呼び出し"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required")

        client = anthropic.Anthropic(api_key=self.api_key)

        message = client.messages.create(
            model=self.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
        )

        return message.content[0].text

    def _complete_openai_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """OpenAI APIをシステムプロンプト付きで呼び出し"""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package is required")

        client = openai.OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model=self.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.choices[0].message.content or ""


class MockLLMClient(BaseLLMClient):
    """テスト用モッククライアント"""

    def __init__(self, responses: Optional[dict[str, str]] = None):
        self.responses = responses or {}
        self.call_history: list[str] = []

    def complete(self, prompt: str) -> str:
        """モックレスポンスを返す"""
        self.call_history.append(prompt)

        # キーワードマッチでレスポンスを選択
        for keyword, response in self.responses.items():
            if keyword in prompt:
                return response

        # デフォルトレスポンス
        return "[INFO] Line 1: Code looks good\n"

    def set_response(self, keyword: str, response: str) -> None:
        """レスポンスを設定"""
        self.responses[keyword] = response
