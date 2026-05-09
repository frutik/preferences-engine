import os

from .memory import DjangoPreferenceMemory
from .providers.factory import get_provider
from .schemas import ExtractionResult, MemoryType, PreferenceSchema, RevisionResult

_DEFAULT_MODEL = os.getenv("PREFERENCE_ENGINE_OPENAI_MODEL", "gpt-5.5")


def render_schema(schema: PreferenceSchema) -> str:
    entity_types = "\n".join(
        f"- {e.name}: {e.description}"
        for e in schema.entity_types
    )

    predicates = "\n".join(
        f"- {p.name}: {p.description}. "
        f"Allowed object types: {', '.join(p.allowed_object_types) or 'any'}"
        for p in schema.predicates
    )

    return f"""
Domain focus:
{schema.domain_focus}

Entity types:
{entity_types}

Predicates:
{predicates}
"""


async def extract_propositions(
    *,
    memory: DjangoPreferenceMemory,
    schema: PreferenceSchema,
    new_messages: list[dict],
    model: str = _DEFAULT_MODEL,
) -> ExtractionResult:
    conversation = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in new_messages
    )

    existing = await memory.existing_for_prompt()

    result = await get_provider().structured_chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"""
You extract durable propositions about the user.

Extract facts about the USER only.

Schema:
{render_schema(schema)}

Rules:
- Extract lasting personal facts, preferences, opinions, requirements, dislikes, constraints, and explicit memory requests.
- Skip greetings, small talk, questions to the assistant, implementation details unless they reveal a stable preference.
- Skip meta-conversation like "can you rewrite this".
- Do not store secrets, credentials, private tokens, or sensitive personal attributes.
- Resolve "I", "me", "my" to the user.
- Use the schema predicates and object types where possible.
- Keep each proposition atomic.
- confidence: explicit statement = high, weak inference = low.
- importance: useful for future personalization = high.
- decay: 0 means durable, 1 means very temporary.
""",
            },
            {
                "role": "user",
                "content": f"""
Known existing propositions:
{existing}

New conversation:
{conversation}
""",
            },
        ],
        response_model=ExtractionResult,
    )

    await memory.log_extraction(result.propositions)
    return result


async def revise_propositions(
    *,
    memory: DjangoPreferenceMemory,
    extracted: ExtractionResult,
    model: str = _DEFAULT_MODEL,
) -> RevisionResult:
    existing = await memory.existing_for_prompt()

    return await get_provider().structured_chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
You revise extracted propositions against an existing memory store.

Actions:
- create: new useful proposition
- reinforce: already known proposition repeated or supported
- merge: new proposition refines or generalizes an existing one
- contradict: new proposition conflicts with existing one
- ignore: proposition is not useful, duplicate noise, too temporary, or unsafe

Prefer reinforce/merge over creating near-duplicates.
Use target_id for reinforce, merge, and contradict.
""",
            },
            {
                "role": "user",
                "content": f"""
Existing memory:
{existing}

Extracted propositions:
{extracted.model_dump_json(indent=2)}
""",
            },
        ],
        response_model=RevisionResult,
    )


async def update_memory_from_turn(
    *,
    readable_memory: DjangoPreferenceMemory,
    global_writable: DjangoPreferenceMemory,
    conversation_writable: DjangoPreferenceMemory,
    schema: PreferenceSchema,
    new_messages: list[dict],
) -> list:
    extracted = await extract_propositions(
        memory=readable_memory,
        schema=schema,
        new_messages=new_messages,
    )

    revision = await revise_propositions(
        memory=readable_memory,
        extracted=extracted,
    )

    # New working-memory creates go to conversation scope; everything else
    # (including reinforce/merge/contradict that reference existing global IDs)
    # goes to the global tier.
    global_patches = []
    conv_patches = []
    for patch in revision.patches:
        if (
            patch.action == "create"
            and patch.proposition is not None
            and patch.proposition.memory_type == MemoryType.working
        ):
            conv_patches.append(patch)
        else:
            global_patches.append(patch)

    changed = await global_writable.apply_revision(
        revision.__class__(patches=global_patches)
    )
    changed += await conversation_writable.apply_revision(
        revision.__class__(patches=conv_patches)
    )
    return changed
