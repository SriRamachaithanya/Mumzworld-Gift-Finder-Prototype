from __future__ import annotations

import json
import os
import re
from urllib import error, request

from pydantic import ValidationError

from src.models import QuerySchema


AGE_PATTERNS = [
    (re.compile(r"(\d+)\s*month", re.IGNORECASE), 1),
    (re.compile(r"(\d+)\s*months", re.IGNORECASE), 1),
    (re.compile(r"(\d+)\s*year", re.IGNORECASE), 12),
    (re.compile(r"(\d+)\s*years", re.IGNORECASE), 12),
    (re.compile(r"(\d+)\s*شهر"), 1),
    (re.compile(r"(\d+)\s*سنة"), 12),
]

BUDGET_PATTERNS = [
    re.compile(r"under\s*(\d+)", re.IGNORECASE),
    re.compile(r"below\s*(\d+)", re.IGNORECASE),
    re.compile(r"budget\s*(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)\s*aed", re.IGNORECASE),
    re.compile(r"أقل من\s*(\d+)"),
    re.compile(r"ميزانية\s*(\d+)"),
]

CATEGORY_KEYWORDS = {
    "feeding": ["bottle", "feeding", "formula", "snack", "رضاعة", "حليب", "سناك"],
    "travel": ["travel", "carrier", "diaper bag", "stroller", "سفر", "حمالة", "حقيبة"],
    "playtime": ["play", "toy", "activity", "gift", "لعبة", "أنشطة", "هدية"],
    "nursery": ["blanket", "swaddle", "nursery", "sleep", "بطانية", "لفافة", "نوم"],
    "mom-care": ["mom", "postpartum", "mother", "أم", "ولادة"],
    "bath": ["bath", "bathtub", "استحمام", "حمام"],
    "development": ["walker", "development", "خطوات", "مشاية"],
}

FILTER_KEYWORDS = {
    "lightweight": ["lightweight", "خفيف"],
    "organic": ["organic", "عضوي"],
    "travel-friendly": ["travel-friendly", "travel friendly", "مناسب للسفر", "للسفر"],
    "safe": ["safe", "آمن"],
    "premium": ["premium", "luxury", "فاخر"],
    "practical": ["practical", "عملي"],
    "newborn": ["newborn", "حديث الولادة"],
}

MEDICAL_KEYWORDS = [
    "fever",
    "rash",
    "vomit",
    "seizure",
    "difficulty breathing",
    "حرارة",
    "طفح",
    "قيء",
    "تشنج",
    "تنفس",
]

ARABIC_LETTERS = re.compile(r"[\u0600-\u06FF]")
DOMAIN_HINTS = {
    "baby",
    "babies",
    "child",
    "children",
    "kid",
    "kids",
    "mom",
    "mother",
    "newborn",
    "toddler",
    "pregnancy",
    "طفل",
    "أطفال",
    "أم",
    "مواليد",
    "رضيع",
    "حامل",
    "هدية",
}
NON_DOMAIN_HINTS = {
    "laptop",
    "phone",
    "mobile",
    "car",
    "crypto",
    "bitcoin",
    "stock",
    "hotel",
    "flight",
    "gaming",
    "restaurant",
    "سهم",
    "سيارة",
    "هاتف",
    "لابتوب",
    "فندق",
    "رحلة",
    "مطعم",
}


def detect_language(text: str) -> str:
    return "ar" if ARABIC_LETTERS.search(text) else "en"


def _extract_age_months(text: str) -> int | None:
    for pattern, multiplier in AGE_PATTERNS:
        match = pattern.search(text)
        if match:
            return int(match.group(1)) * multiplier
    return None


def _extract_budget(text: str) -> int | None:
    for pattern in BUDGET_PATTERNS:
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


def _extract_category(text: str) -> str | None:
    lowered = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return None


def _extract_filters(text: str) -> list[str]:
    lowered = text.lower()
    filters: list[str] = []
    for label, keywords in FILTER_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            filters.append(label)
    return filters


def _extract_intent(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["gift", "هدية"]):
        return "gift"
    if any(word in lowered for word in ["recommend", "suggest", "اقترح", "ترشيح"]):
        return "recommendation"
    return "search"


def _confidence_label(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _is_domain_related(text: str, category: str | None, filters: list[str], age_months: int | None) -> bool:
    lowered = text.lower()
    if category is not None or bool(filters) or age_months is not None:
        return True
    if any(hint in lowered for hint in DOMAIN_HINTS):
        return True
    return False


def _is_explicitly_non_domain(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in NON_DOMAIN_HINTS)


def _needs_clarification(text: str, intent: str, category: str | None) -> tuple[bool, str | None]:
    short_query = len(text.split()) < 3
    if short_query or (intent != "gift" and category is None):
        return True, {
            "en": "Could you share the product type, age of the child, or budget?",
            "ar": "هل يمكنك توضيح نوع المنتج أو عمر الطفل أو الميزانية؟",
        }[detect_language(text)]
    return False, None


def heuristic_extract(query: str) -> QuerySchema:
    language = detect_language(query)
    safety_flag = "medical" if any(word in query.lower() for word in MEDICAL_KEYWORDS) else "ok"
    intent = _extract_intent(query)
    category = _extract_category(query)
    age_months = _extract_age_months(query)
    budget_aed = _extract_budget(query)
    filters = _extract_filters(query)
    out_of_domain = _is_explicitly_non_domain(query) and not _is_domain_related(query, category, filters, age_months)
    clarification_needed, clarification_question = _needs_clarification(query, intent, category)
    if out_of_domain:
        clarification_needed = False
        clarification_question = None

    confidence = 0.9
    if out_of_domain:
        confidence = 0.2
    elif clarification_needed:
        confidence = 0.45
    elif category is None:
        confidence = 0.65
    confidence_label = _confidence_label(confidence)

    clean_category = category or "general"
    search_query = " | ".join(
        [
            clean_category,
            f"age:{age_months}" if age_months is not None else "age:any",
            f"budget:{budget_aed}" if budget_aed is not None else "budget:any",
            ",".join(filters) if filters else "filters:none",
        ]
    )

    return QuerySchema(
        original_query=query,
        language=language,
        intent=intent,
        category=category,
        age_months=age_months,
        budget_aed=budget_aed,
        filters=filters,
        search_query=search_query,
        confidence=confidence,
        confidence_label=confidence_label,
        clarification_needed=clarification_needed,
        clarification_question=clarification_question,
        safety_flag=safety_flag,
        out_of_domain=out_of_domain,
    )


def llm_extract(query: str) -> QuerySchema | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    prompt = f"""
You extract shopping intent for a Mumzworld-like gift finder.
Return JSON only with keys:
language, intent, category, age_months, budget_aed, filters, search_query, confidence, confidence_label, clarification_needed, clarification_question, safety_flag, out_of_domain

Rules:
- intent must be one of search, gift, recommendation
- safety_flag must be ok or medical
- budget_aed must be null if not explicit
- If the query is too vague, set clarification_needed true
- confidence_label must be one of high, medium, low
- If query is unrelated to mother/baby products, set out_of_domain true
- Arabic output values should still use schema-friendly English labels except clarification_question may be Arabic

User query: {query}
""".strip()

    payload = {
        "model": os.getenv("OPENROUTER_MODEL", "qwen/qwen3-14b:free"),
        "messages": [
            {"role": "system", "content": "You are a precise extraction engine. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }

    req = request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "mumzworld-gift-finder",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        parsed["original_query"] = query
        if "confidence_label" not in parsed and "confidence" in parsed:
            parsed["confidence_label"] = _confidence_label(float(parsed["confidence"]))
        if "out_of_domain" not in parsed:
            parsed["out_of_domain"] = False
        return QuerySchema.model_validate(parsed)
    except (error.URLError, TimeoutError, KeyError, json.JSONDecodeError, ValidationError):
        return None


def extract_query(query: str) -> QuerySchema:
    llm_result = llm_extract(query)
    if llm_result is not None:
        return llm_result
    return heuristic_extract(query)
