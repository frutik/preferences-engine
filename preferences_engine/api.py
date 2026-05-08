import logging
from typing import List
from uuid import UUID

from ninja import Router
from ninja.pagination import paginate

from .api_schemas import UserPreferenceMemorySchema
from .models import UserPreferenceMemory

logger = logging.getLogger(__name__)

router = Router(tags=["User Preferences"])


@router.get("/preferences/", response={200: List[UserPreferenceMemorySchema], 403: str})
@paginate
async def preferences(request):
    if not request.auth:
        return 403, "Unauthorized"
    return UserPreferenceMemory.objects\
        .select_related("user")\
        .filter(user__key=request.auth)


@router.delete("/preferences/{preference_id}/", response={204: None, 403: str, 404: str})
async def delete_preference(request, preference_id: UUID):
    if not request.auth:
        return 403, "Unauthorized"
    deleted, _ = await UserPreferenceMemory.objects.filter(
        id=preference_id,
        user__key=request.auth,
    ).adelete()
    if not deleted:
        return 404, "Not found"
    return 204, None
