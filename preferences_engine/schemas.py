from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    semantic = "semantic"
    procedural = "procedural"
    episodic = "episodic"
    working = "working"


class DomainEntityType(BaseModel):
    name: str
    description: str


class DomainPredicate(BaseModel):
    name: str
    description: str
    allowed_object_types: list[str] = []


class PreferenceSchema(BaseModel):
    domain_focus: str
    entity_types: list[DomainEntityType]
    predicates: list[DomainPredicate]


class ExtractedProposition(BaseModel):
    text: str

    subject: str = ""
    predicate: str = ""
    object: str = ""
    object_type: str = ""

    memory_type: MemoryType = MemoryType.semantic

    confidence: float = Field(ge=0, le=1)
    importance: float = Field(ge=0, le=1)
    decay: float = Field(ge=0, le=1)

    reasoning: str = ""
    evidence: str = ""


class ExtractionResult(BaseModel):
    propositions: list[ExtractedProposition]


class PropositionPatch(BaseModel):
    action: Literal["create", "reinforce", "merge", "contradict", "ignore"]
    target_id: UUID | None = None
    proposition: ExtractedProposition | None = None
    reasoning: str = ""


class RevisionResult(BaseModel):
    patches: list[PropositionPatch]
