from __future__ import annotations

import json

from src.catalog import load_catalog
from src.extractor import extract_query
from src.models import RecommendationResponse
from src.recommender import recommend_products


def run_pipeline(user_query: str) -> RecommendationResponse:
    catalog = load_catalog()
    query = extract_query(user_query)
    return recommend_products(catalog, query)


def render_text_response(result: RecommendationResponse) -> str:
    structured = result.structured_data.model_dump()
    lines = [
        "SECTION 1: STRUCTURED DATA",
        json.dumps(structured, ensure_ascii=False, indent=2),
        "",
        "SECTION 2: RECOMMENDATIONS",
    ]

    if result.refusal_message:
        lines.append(result.refusal_message)
        return "\n".join(lines)

    if result.structured_data.clarification_needed and result.structured_data.clarification_question:
        lines.append(result.structured_data.clarification_question)
        return "\n".join(lines)

    for index, item in enumerate(result.recommendations, start=1):
        lines.append(f"{index}. {item.product_name}")
        lines.append(f"   - {item.why_it_fits}")
        lines.append(f"   - {item.budget_suitability}")
        if item.evidence:
            lines.append(f"   - Evidence: {'; '.join(item.evidence)}")
        lines.append("")

    return "\n".join(lines).strip()
