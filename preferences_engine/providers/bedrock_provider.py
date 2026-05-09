import os

try:
    from anthropic import AsyncAnthropicBedrock
except ImportError as e:
    raise ImportError(
        "Bedrock provider requires: pip install 'preferences-engine[bedrock]'"
    ) from e

from .anthropic_provider import AnthropicProvider


class BedrockProvider(AnthropicProvider):
    def __init__(self):
        self._client = AsyncAnthropicBedrock(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
        )
