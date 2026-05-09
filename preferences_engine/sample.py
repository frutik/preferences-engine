import os

from openai import AsyncOpenAI

_client_kwargs = {"api_key": os.getenv("PREFERENCE_ENGINE_OPENAI_API_KEY")}
if _base_url := os.getenv("PREFERENCE_ENGINE_OPENAI_BASE_URL"):
    _client_kwargs["base_url"] = _base_url
client = AsyncOpenAI(**_client_kwargs)

_DEFAULT_MODEL = os.getenv("PREFERENCE_ENGINE_OPENAI_MODEL", "gpt-5.5")


async def generate_answer(
    *,
    user_message: str,
    history: list[dict],
    memory_context: str,
):
    response = await client.chat.completions.create(
        model=_DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""
You are a shopping assistant.

Known user preferences:
{memory_context}

Use these preferences only when relevant.
Do not mention memory unless debug mode is enabled.
""",
            },
            *history,
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content
