from .domain_schema import SHOPPING_PREFERENCE_SCHEMA
from .extraction import update_memory_from_turn
from .memory import DjangoPreferenceMemory
from .sample import generate_answer


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

    # Extract before answer generation, so the current message can affect this turn.
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
