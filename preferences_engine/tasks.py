import logging
import asyncio

from celery import shared_task

from .memory import DjangoPreferenceMemory
from .domain_schema import SHOPPING_PREFERENCE_SCHEMA
from .extraction import update_memory_from_turn as memory_updater

logger = logging.getLogger(__name__)

@shared_task(ignore_result=True)
def update_memory_from_turn(user, conversation_id, message):
    asyncio.run(_update_memory_from_turn(user, conversation_id, message))


async def _update_memory_from_turn(user, conversation_id, message):
    readable_memory = await DjangoPreferenceMemory.for_user_key(
        user_key=user,
        conversation_id=conversation_id,
        include_global=True,
    )
    global_writable = DjangoPreferenceMemory(
        user=readable_memory.user,
        conversation_id=None,
    )
    conversation_writable = DjangoPreferenceMemory(
        user=readable_memory.user,
        conversation_id=conversation_id,
    )
    extracted_messages = [
        {"role": "user", "content": message},
    ]
    changed = await memory_updater(
        readable_memory=readable_memory,
        global_writable=global_writable,
        conversation_writable=conversation_writable,
        schema=SHOPPING_PREFERENCE_SCHEMA,
        new_messages=extracted_messages,
    )
    logger.info(['known preferences change', readable_memory.user, changed])

    changed = await memory_updater(
        readable_memory=readable_memory,
        global_writable=global_writable,
        conversation_writable=conversation_writable,
        schema=SHOPPING_PREFERENCE_SCHEMA,
        new_messages=extracted_messages,
    )
    logger.info(['known preferences change', readable_memory.user, changed])
