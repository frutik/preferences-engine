# admin.py
from django import forms
from django.contrib import admin

from .domain_schema import SHOPPING_PREFERENCE_SCHEMA
from .models import (
    MemoryUser,
    UserPreferenceMemory,
    UserPreferenceMemoryEvent,
)

_ENTITY_TYPE_CHOICES = [("", "---------")] + [
    (e.name, e.name) for e in SHOPPING_PREFERENCE_SCHEMA.entity_types
]

_PREDICATE_CHOICES = [("", "---------")] + [
    (p.name, p.name) for p in SHOPPING_PREFERENCE_SCHEMA.predicates
]


class UserPreferenceMemoryForm(forms.ModelForm):
    subject = forms.ChoiceField(choices=_ENTITY_TYPE_CHOICES, required=False)
    predicate = forms.ChoiceField(choices=_PREDICATE_CHOICES, required=False)
    object_type = forms.ChoiceField(choices=_ENTITY_TYPE_CHOICES, required=False)

    class Meta:
        model = UserPreferenceMemory
        fields = "__all__"


class UserPreferenceMemoryInline(admin.TabularInline):
    model = UserPreferenceMemory
    extra = 0
    fields = (
        "text",
        "conversation_id",
        "memory_type",
        "status",
        "confidence",
        "importance",
        "decay",
        "updated_at",
    )
    readonly_fields = ("updated_at",)
    show_change_link = True


class UserPreferenceMemoryEventInline(admin.TabularInline):
    model = UserPreferenceMemoryEvent
    extra = 0
    fields = (
        "action",
        "conversation_id",
        "memory",
        "reasoning",
        "created_at",
    )
    readonly_fields = ("created_at",)
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MemoryUser)
class MemoryUserAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "display_name",
        "memories_count",
        "events_count",
        "created_at",
        "updated_at",
    )
    search_fields = ("key", "display_name")
    readonly_fields = ("id", "created_at", "updated_at")

    inlines = (
        UserPreferenceMemoryInline,
        UserPreferenceMemoryEventInline,
    )

    def memories_count(self, obj):
        return obj.memories.count()

    def events_count(self, obj):
        return obj.memory_events.count()


class PreferenceMemoryEventForMemoryInline(admin.TabularInline):
    model = UserPreferenceMemoryEvent
    extra = 0
    fields = (
        "action",
        "conversation_id",
        "reasoning",
        "evidence",
        "created_at",
    )
    readonly_fields = (
        "action",
        "conversation_id",
        "reasoning",
        "evidence",
        "created_at",
    )
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(UserPreferenceMemory)
class UserPreferenceMemoryAdmin(admin.ModelAdmin):
    form = UserPreferenceMemoryForm
    list_display = (
        "text_short",
        "user",
        "conversation_scope",
        "predicate",
        "object",
        "object_type",
        "memory_type",
        "status",
        "score",
        "confidence",
        "importance",
        "decay",
        "updated_at",
    )
    list_filter = (
        "memory_type",
        "status",
        "predicate",
        "object_type",
        ("conversation_id", admin.EmptyFieldListFilter),
    )
    search_fields = (
        "text",
        "subject",
        "predicate",
        "object",
        "object_type",
        "reasoning",
        "evidence",
        "user__key",
        "user__display_name",
        "conversation_id",
    )
    readonly_fields = (
        "id",
        "score",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("user",)
    ordering = ("-updated_at",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "user",
                    "conversation_id",
                    "text",
                    "status",
                )
            },
        ),
        (
            "Domain proposition",
            {
                "fields": (
                    "subject",
                    "predicate",
                    "object",
                    "object_type",
                )
            },
        ),
        (
            "Scoring",
            {
                "fields": (
                    "memory_type",
                    "confidence",
                    "importance",
                    "decay",
                    "score",
                )
            },
        ),
        (
            "Evidence",
            {
                "fields": (
                    "reasoning",
                    "evidence",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = (
        PreferenceMemoryEventForMemoryInline,
    )

    def text_short(self, obj):
        return obj.text[:100]

    def conversation_scope(self, obj):
        if obj.conversation_id is None:
            return "global"
        return obj.conversation_id

    def score(self, obj):
        return round(obj.importance * obj.confidence, 4)


@admin.register(UserPreferenceMemoryEvent)
class UserPreferenceMemoryEventAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "user",
        "memory",
        "conversation_scope",
        "created_at",
    )
    list_filter = (
        "action",
        ("conversation_id", admin.EmptyFieldListFilter),
        "created_at",
    )
    search_fields = (
        "user__key",
        "user__display_name",
        "memory__text",
        "reasoning",
        "evidence",
        "conversation_id",
    )
    readonly_fields = (
        "id",
        "created_at",
        "payload_pretty",
    )
    autocomplete_fields = (
        "user",
        "memory",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "user",
                    "memory",
                    "conversation_id",
                    "action",
                    "created_at",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "reasoning",
                    "evidence",
                    "payload_pretty",
                )
            },
        ),
    )

    def conversation_scope(self, obj):
        if obj.conversation_id is None:
            return "global"
        return obj.conversation_id

    def payload_pretty(self, obj):
        import json
        from django.utils.html import format_html

        return format_html(
            "<pre style='white-space: pre-wrap'>{}</pre>",
            json.dumps(obj.payload, indent=2, ensure_ascii=False),
        )
