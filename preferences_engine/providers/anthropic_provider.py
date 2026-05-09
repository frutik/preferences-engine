import os

from anthropic import AsyncAnthropic
from pydantic import BaseModel


class AnthropicProvider:
    def __init__(self):
        self._client = AsyncAnthropic(
            api_key=os.getenv("PREFERENCE_ENGINE_ANTHROPIC_API_KEY")
        )

    def _split_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        system_parts = []
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_parts.append(m["content"])
            else:
                filtered.append(m)
        return "\n\n".join(system_parts), filtered

    async def structured_chat(
        self,
        messages: list[dict],
        model: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        system, filtered = self._split_messages(messages)
        tool = {
            "name": "output",
            "description": f"Output the result as {response_model.__name__}",
            "input_schema": response_model.model_json_schema(),
        }
        response = await self._client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=filtered,
            tools=[tool],
            tool_choice={"type": "tool", "name": "output"},
        )
        for block in response.content:
            if block.type == "tool_use":
                return response_model.model_validate(block.input)
        raise RuntimeError("Anthropic returned no tool_use block")
