import os

from openai import AsyncOpenAI

from .domain_schema import SHOPPING_PREFERENCE_SCHEMA
from .extraction import update_memory_from_turn
from .memory import DjangoPreferenceMemory

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


async def chat_turn(
    *,
    user_key: str,
    conversation_id: str,
    user_message: str,
    history: list[dict],
    debug_memory: bool = False,
):
    readable_memory = await DjangoPreferenceMemory.for_user_key(
        user_key=user_key,
        conversation_id=conversation_id,
        include_global=True,
    )

    extracted_messages = [
        {"role": "user", "content": user_message},
    ]

    writable_memory = DjangoPreferenceMemory(
        user=readable_memory.user,
        conversation_id=None,  # durable/global memory
    )

    changed = await update_memory_from_turn(
        readable_memory=readable_memory,
        writable_memory=writable_memory,
        schema=SHOPPING_PREFERENCE_SCHEMA,
        new_messages=extracted_messages,
    )

    memory_context = await readable_memory.inject_for_prompt(limit=20)

    answer = await generate_answer(
        user_message=user_message,
        history=history,
        memory_context=memory_context,
    )

    history.extend(
        [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer},
        ]
    )

    if debug_memory and changed:
        learned = "; ".join(m.text for m in changed[:3])
        answer += f"\n\n[learned: {learned}]"

    return answer
