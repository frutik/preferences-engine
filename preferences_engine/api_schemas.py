from ninja import ModelSchema

from .models import MemoryUser, UserPreferenceMemory


class MemoryUserSchema(ModelSchema):
    class Meta:
        model = MemoryUser
        fields = ["key", "display_name", "created_at", "updated_at"]


class UserPreferenceMemorySchema(ModelSchema):
    class Meta:
        model = UserPreferenceMemory
        fields = [
            "id",
            # "conversation_id",
            # "text",
            "subject",
            "predicate",
            "object",
            "object_type",
            "memory_type",
            "confidence",
            "importance",
            # "decay",
            # "reasoning",
            # "evidence",
            # "status",
            "created_at",
            "updated_at",
        ]


# class UserPreferenceMemoryEventSchema(ModelSchema):
#     class Meta:
#         model = UserPreferenceMemoryEvent
#         fields = [
#             "id",
#             "conversation_id",
#             "action",
#             "payload",
#             "reasoning",
#             "evidence",
#             "created_at",
#         ]
