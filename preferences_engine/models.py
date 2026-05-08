import math
import uuid

from django.db import models
from django.utils import timezone

DECAY_THRESHOLD = 0.05


class MemoryUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    key = models.CharField(max_length=255, unique=True, db_index=True)
    display_name = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("key",)

    def __str__(self):
        return self.display_name or self.key


class UserPreferenceMemory(models.Model):
    class MemoryType(models.TextChoices):
        SEMANTIC = "semantic", "Semantic"
        PROCEDURAL = "procedural", "Procedural"
        EPISODIC = "episodic", "Episodic"
        WORKING = "working", "Working"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUPERSEDED = "superseded", "Superseded"
        CONTRADICTED = "contradicted", "Contradicted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        MemoryUser,
        on_delete=models.CASCADE,
        related_name="memories",
    )

    # NULL = global / long-term memory
    conversation_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
    )

    text = models.TextField()

    # Domain-aware fields
    subject = models.CharField(max_length=255, blank=True)      # Customer / user name
    predicate = models.CharField(max_length=128, blank=True)    # prefers, dislikes, owns, needs
    object = models.CharField(max_length=255, blank=True)       # Sony, protein bars, cheap delivery
    object_type = models.CharField(max_length=128, blank=True)  # Brand, Category, Feature

    memory_type = models.CharField(
        max_length=32,
        choices=MemoryType.choices,
        default=MemoryType.SEMANTIC,
        db_index=True,
    )

    confidence = models.FloatField(default=0.5)
    importance = models.FloatField(default=0.5)
    decay = models.FloatField(default=0.2)

    reasoning = models.TextField(blank=True)
    evidence = models.TextField(blank=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "conversation_id", "status"]),
            models.Index(fields=["user", "predicate", "object"]),
            models.Index(fields=["memory_type", "status"]),
        ]

    def score(self) -> float:
        return self.importance * self.confidence

    def effective_score(self, now=None) -> float:
        now = now or timezone.now()
        age_months = (now - self.updated_at).total_seconds() / (30 * 24 * 3600)
        return self.importance * self.confidence * math.exp(-self.decay * age_months)

    def __str__(self):
        return self.text[:120]


class UserPreferenceMemoryEvent(models.Model):
    class Action(models.TextChoices):
        EXTRACT = "extract", "Extract"
        CREATE = "create", "Create"
        REINFORCE = "reinforce", "Reinforce"
        MERGE = "merge", "Merge"
        CONTRADICT = "contradict", "Contradict"
        IGNORE = "ignore", "Ignore"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        MemoryUser,
        on_delete=models.CASCADE,
        related_name="memory_events",
    )

    memory = models.ForeignKey(
        UserPreferenceMemory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
    )

    conversation_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
    )

    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    reasoning = models.TextField(blank=True)
    evidence = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "conversation_id", "created_at"]),
            models.Index(fields=["memory", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]
