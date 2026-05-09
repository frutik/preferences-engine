from typing import Protocol, runtime_checkable

from pydantic import BaseModel


@runtime_checkable
class LLMProvider(Protocol):
    async def structured_chat(
        self,
        messages: list[dict],
        model: str,
        response_model: type[BaseModel],
    ) -> BaseModel: ...
