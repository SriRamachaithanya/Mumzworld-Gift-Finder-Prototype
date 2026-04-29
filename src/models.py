from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


SUPPORTED_INTENTS = {"search", "gift", "recommendation"}
SUPPORTED_LANGUAGES = {"en", "ar"}


class QuerySchema(BaseModel):
    original_query: str = Field(min_length=2)
    language: Literal["en", "ar"]
    intent: Literal["search", "gift", "recommendation"]
    category: str | None = None
    age_months: int | None = Field(default=None, ge=0, le=144)
    budget_aed: int | None = Field(default=None, ge=1, le=10000)
    filters: list[str] = Field(default_factory=list)
    search_query: str = Field(min_length=2)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: Literal["high", "medium", "low"] = "medium"
    clarification_needed: bool = False
    clarification_question: str | None = None
    safety_flag: Literal["ok", "medical"] = "ok"
    out_of_domain: bool = False

    @field_validator("filters")
    @classmethod
    def normalize_filters(cls, values: list[str]) -> list[str]:
        return sorted({value.strip().lower() for value in values if value and value.strip()})

    @model_validator(mode="after")
    def validate_clarification(self) -> "QuerySchema":
        if self.clarification_needed and not self.clarification_question:
            raise ValueError("clarification_question is required when clarification_needed is true")
        return self


class Product(BaseModel):
    id: str
    name_en: str
    name_ar: str
    category: str
    price_aed: int
    age_min_months: int
    age_max_months: int
    tags: list[str]
    persona: list[str]
    description_en: str
    description_ar: str
    relevance_terms: list[str]


class Recommendation(BaseModel):
    product_id: str
    product_name: str
    why_it_fits: str
    budget_suitability: str
    price_aed: int = Field(ge=0)
    evidence: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0)


class RecommendationResponse(BaseModel):
    structured_data: QuerySchema
    recommendations: list[Recommendation]
    refusal_message: str | None = None
    retrieval_note: str | None = None
