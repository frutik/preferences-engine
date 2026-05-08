import os

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("PREFERENCE_ENGINE_OPENAI_API_KEY"))


async def generate_answer(
    *,
    user_message: str,
    history: list[dict],
    memory_context: str,
):
    response = await client.responses.create(
        model="gpt-5.5",
        input=[
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

    return response.output_text
