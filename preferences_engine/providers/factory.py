import os

from .base import LLMProvider

_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        name = os.getenv("PREFERENCE_ENGINE_PROVIDER", "openai")
        if name == "openai":
            from .openai_provider import OpenAIProvider
            _provider = OpenAIProvider()
        elif name == "anthropic":
            from .anthropic_provider import AnthropicProvider
            _provider = AnthropicProvider()
        elif name == "bedrock":
            from .bedrock_provider import BedrockProvider
            _provider = BedrockProvider()
        else:
            raise ValueError(f"Unknown provider: {name!r}")
    return _provider
