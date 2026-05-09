import os

from anthropic import AsyncAnthropicBedrock

from .anthropic_provider import AnthropicProvider


class BedrockProvider(AnthropicProvider):
    def __init__(self):
        self._client = AsyncAnthropicBedrock(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
        )
