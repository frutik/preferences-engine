from django.db import transaction
from django.db.models import Q

from .models import DECAY_THRESHOLD, MemoryUser, UserPreferenceMemory, UserPreferenceMemoryEvent
from .schemas import ExtractedProposition, RevisionResult


class DjangoPreferenceMemory:
    def __init__(
        self,
        *,
        user: MemoryUser,
        conversation_id: str | None = None,
        include_global: bool = True,
    ):
        self.user = user
        self.conversation_id = conversation_id
        self.include_global = include_global

    @classmethod
    async def for_user_key(
        cls,
        *,
        user_key: str,
        display_name: str = "",
        conversation_id: str | None = None,
        include_global: bool = True,
    ):
        user, _ = await MemoryUser.objects.aget_or_create(
            key=user_key,
            defaults={"display_name": display_name},
        )

        return cls(
            user=user,
            conversation_id=conversation_id,
            include_global=include_global,
        )

    def queryset(self):
        qs = UserPreferenceMemory.objects.filter(user=self.user)

        if self.conversation_id is None:
            return qs.filter(conversation_id__isnull=True)

        if self.include_global:
            return qs.filter(
                Q(conversation_id=self.conversation_id)
                | Q(conversation_id__isnull=True)
            )

        return qs.filter(conversation_id=self.conversation_id)

    async def active(self):
        qs = self.queryset().filter(
            status=UserPreferenceMemory.Status.ACTIVE
        )
        return [obj async for obj in qs]

    async def existing_for_prompt(self, limit: int = 50) -> str:
        items = await self.active()
        items = [p for p in items if p.effective_score() >= DECAY_THRESHOLD]
        items.sort(key=lambda p: p.effective_score(), reverse=True)

        if not items:
            return "No existing propositions."

        return "\n".join(
            f"{p.id}: {p.text} "
            f"(subject={p.subject}, predicate={p.predicate}, object={p.object}, "
            f"type={p.object_type}, confidence={p.confidence:.2f}, "
            f"importance={p.importance:.2f}, decay={p.decay:.2f})"
            for p in items[:limit]
        )

    async def inject_for_prompt(self, limit: int = 20) -> str:
        items = await self.active()
        items = [p for p in items if p.effective_score() >= DECAY_THRESHOLD]
        items.sort(key=lambda p: p.effective_score(), reverse=True)

        if not items:
            return "No known user preferences yet."

        return "\n".join(
            f"- {p.text}"
            for p in items[:limit]
        )

    async def log_extraction(self, propositions: list[ExtractedProposition]) -> None:
        await UserPreferenceMemoryEvent.objects.acreate(
            user=self.user,
            conversation_id=self.conversation_id,
            action=UserPreferenceMemoryEvent.Action.EXTRACT,
            payload={
                "propositions": [
                    p.model_dump(mode="json") for p in propositions
                ]
            },
        )

    async def apply_revision(self, revision: RevisionResult) -> list[UserPreferenceMemory]:
        # async with transaction.aatomic():
        # with transaction.atomic():
        return await self._apply_revision(revision)

    async def _apply_revision(self, revision: RevisionResult) -> list[UserPreferenceMemory]:
        changed = []

        for patch in revision.patches:
            memory = None

            if patch.action == "ignore":
                await self._log_event(
                    action=patch.action,
                    memory=None,
                    payload=patch.model_dump(mode="json"),
                    reasoning=patch.reasoning,
                )
                continue

            if patch.action == "create":
                if not patch.proposition:
                    await self._log_event(
                        action=patch.action,
                        memory=None,
                        payload=patch.model_dump(mode="json"),
                        reasoning="Skipped create: missing proposition",
                    )
                    continue

                p = patch.proposition

                memory = await UserPreferenceMemory.objects.acreate(
                    user=self.user,
                    conversation_id=self.conversation_id,
                    text=p.text,
                    subject=p.subject,
                    predicate=p.predicate,
                    object=p.object,
                    object_type=p.object_type,
                    memory_type=p.memory_type.value,
                    confidence=p.confidence,
                    importance=p.importance,
                    decay=p.decay,
                    reasoning=p.reasoning,
                    evidence=p.evidence,
                )

                changed.append(memory)

                await self._log_event(
                    action=patch.action,
                    memory=memory,
                    payload=patch.model_dump(mode="json"),
                    reasoning=patch.reasoning,
                    evidence=p.evidence,
                )
                continue

            if not patch.target_id:
                await self._log_event(
                    action=patch.action,
                    memory=None,
                    payload=patch.model_dump(mode="json"),
                    reasoning="Skipped patch: missing target_id",
                )
                continue

            try:
                memory = await (
                    self.queryset()
                    # .select_for_update()
                    .aget(id=patch.target_id)
                )
            except UserPreferenceMemory.DoesNotExist:
                await self._log_event(
                    action=patch.action,
                    memory=None,
                    payload=patch.model_dump(mode="json"),
                    reasoning=f"Skipped patch: target not found: {patch.target_id}",
                )
                continue

            if patch.action == "reinforce":
                memory.confidence = min(1.0, memory.confidence + 0.08)

                if patch.proposition:
                    memory.importance = max(
                        memory.importance,
                        patch.proposition.importance,
                    )

                memory.reasoning = append_note(
                    memory.reasoning,
                    f"Reinforced: {patch.reasoning}",
                )

                await memory.asave(
                    update_fields=[
                        "confidence",
                        "importance",
                        "reasoning",
                        "updated_at",
                    ]
                )

            elif patch.action == "merge":
                if not patch.proposition:
                    continue

                p = patch.proposition

                memory.text = p.text
                memory.subject = p.subject
                memory.predicate = p.predicate
                memory.object = p.object
                memory.object_type = p.object_type
                memory.memory_type = p.memory_type.value
                memory.confidence = max(memory.confidence, p.confidence)
                memory.importance = max(memory.importance, p.importance)
                memory.decay = min(memory.decay, p.decay)

                memory.reasoning = append_note(
                    memory.reasoning,
                    f"Merged: {patch.reasoning}",
                )
                memory.evidence = append_note(memory.evidence, p.evidence)

                await memory.asave()

            elif patch.action == "contradict":
                memory.status = UserPreferenceMemory.Status.CONTRADICTED
                memory.reasoning = append_note(
                    memory.reasoning,
                    f"Contradicted: {patch.reasoning}",
                )
                await memory.asave(update_fields=["status", "reasoning", "updated_at"])

            changed.append(memory)

            await self._log_event(
                action=patch.action,
                memory=memory,
                payload=patch.model_dump(mode="json"),
                reasoning=patch.reasoning,
                evidence=patch.proposition.evidence if patch.proposition else "",
            )

        return changed

    async def _log_event(
        self,
        *,
        action: str,
        memory: UserPreferenceMemory | None,
        payload: dict,
        reasoning: str = "",
        evidence: str = "",
    ) -> None:
        await UserPreferenceMemoryEvent.objects.acreate(
            user=self.user,
            conversation_id=self.conversation_id,
            memory=memory,
            action=action,
            payload=payload,
            reasoning=reasoning or "",
            evidence=evidence or "",
        )


def append_note(existing: str, note: str) -> str:
    note = (note or "").strip()

    if not note:
        return existing or ""

    if not existing:
        return note

    return f"{existing}\n{note}"
