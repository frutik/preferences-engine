import os

from openai import AsyncOpenAI
from pydantic import BaseModel


class OpenAIProvider:
    def __init__(self):
        kwargs = {"api_key": os.getenv("PREFERENCE_ENGINE_OPENAI_API_KEY")}
        if base_url := os.getenv("PREFERENCE_ENGINE_OPENAI_BASE_URL"):
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)

    async def structured_chat(
        self,
        messages: list[dict],
        model: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        response = await self._client.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=response_model,
        )
        return response.choices[0].message.parsed
