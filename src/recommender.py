from __future__ import annotations

from src.models import Product, QuerySchema, Recommendation, RecommendationResponse


def _confidence_label(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _token_overlap_count(query_text: str, product: Product) -> int:
    product_text = " ".join(
        [
            product.name_en.lower(),
            product.description_en.lower(),
            " ".join(term.lower() for term in product.relevance_terms),
            " ".join(tag.lower() for tag in product.tags),
        ]
    )
    return sum(1 for token in query_text.split() if len(token) > 2 and token in product_text)


def _score_product(product: Product, query: QuerySchema) -> float:
    score = 0.0
    if query.category and product.category == query.category:
        score += 3.0
    if query.age_months is not None and product.age_min_months <= query.age_months <= product.age_max_months:
        score += 2.5
    elif query.age_months is None:
        score += 0.75

    if query.budget_aed is not None:
        if product.price_aed <= query.budget_aed:
            score += 2.0
        else:
            score -= 4.0

    for item_filter in query.filters:
        if item_filter in product.tags:
            score += 1.25

    query_text = query.original_query.lower()
    token_overlap = _token_overlap_count(query_text, product)
    score += 0.15 * token_overlap

    if query.intent == "gift" and "gift" in product.tags:
        score += 1.0

    return round(score, 3)


def _budget_note(price_aed: int, budget_aed: int | None, language: str) -> str:
    if budget_aed is None:
        return "No budget was provided." if language == "en" else "لم يتم تحديد ميزانية."
    if price_aed <= budget_aed:
        return (
            f"Within the {budget_aed} AED budget."
            if language == "en"
            else f"ضمن ميزانية {budget_aed} درهم."
        )
    return (
        f"Above the {budget_aed} AED budget, so it is included only as a stretch option."
        if language == "en"
        else f"أعلى من ميزانية {budget_aed} درهم، لذلك تم إدراجه كخيار ممتد فقط."
    )


def _evidence(product: Product, query: QuerySchema) -> list[str]:
    evidence: list[str] = []
    if query.category and query.category == product.category:
        evidence.append(
            f"Category match: {product.category}"
            if query.language == "en"
            else f"تطابق الفئة: {product.category}"
        )
    if query.age_months is not None and product.age_min_months <= query.age_months <= product.age_max_months:
        if query.language == "en":
            evidence.append(f"Age fit: {product.age_min_months}-{product.age_max_months} months")
        else:
            evidence.append(f"ملاءمة العمر: من {product.age_min_months} إلى {product.age_max_months} شهرًا")
    if query.budget_aed is not None and product.price_aed <= query.budget_aed:
        evidence.append(
            f"Budget fit: {product.price_aed} AED <= {query.budget_aed} AED"
            if query.language == "en"
            else f"ملاءمة الميزانية: {product.price_aed} <= {query.budget_aed} درهم"
        )

    matched_filters = [item for item in query.filters if item in product.tags]
    if matched_filters:
        evidence.append(
            "Matched filters: " + ", ".join(matched_filters)
            if query.language == "en"
            else "الخصائص المطابقة: " + "، ".join(matched_filters)
        )

    if not evidence:
        evidence.append(product.description_ar if query.language == "ar" else product.description_en)
    return evidence


def _why_it_fits(product: Product, query: QuerySchema) -> str:
    if query.language == "ar":
        reasons: list[str] = []
        if query.age_months is not None and product.age_min_months <= query.age_months <= product.age_max_months:
            reasons.append("مناسب للعمر المذكور")
        if query.category and query.category == product.category:
            reasons.append("ينتمي للفئة المطلوبة")
        if query.filters:
            matched = [item for item in query.filters if item in product.tags]
            if matched:
                reasons.append("يلبي بعض الشروط مثل " + "، ".join(matched))
        if not reasons:
            reasons.append(product.description_ar)
        return "، ".join(reasons)

    reasons_en: list[str] = []
    if query.age_months is not None and product.age_min_months <= query.age_months <= product.age_max_months:
        reasons_en.append("matches the child's age")
    if query.category and query.category == product.category:
        reasons_en.append("fits the requested category")
    if query.filters:
        matched = [item for item in query.filters if item in product.tags]
        if matched:
            reasons_en.append("covers filters like " + ", ".join(matched))
    if not reasons_en:
        reasons_en.append(product.description_en)
    return ", ".join(reasons_en)


def recommend_products(catalog: list[Product], query: QuerySchema) -> RecommendationResponse:
    if query.safety_flag == "medical":
        refusal_message = (
            "I can't help with medical triage. Please consult a doctor or pediatrician."
            if query.language == "en"
            else "لا أستطيع تقديم فرز طبي. يرجى استشارة طبيب أو طبيب أطفال."
        )
        return RecommendationResponse(
            structured_data=query,
            recommendations=[],
            refusal_message=refusal_message,
        )

    if query.out_of_domain:
        query.confidence = min(query.confidence, 0.2)
        query.confidence_label = "low"
        return RecommendationResponse(
            structured_data=query,
            recommendations=[],
            refusal_message="I don't know" if query.language == "en" else "لا أعرف",
        )

    if query.clarification_needed:
        query.confidence = min(query.confidence, 0.4)
        query.confidence_label = "low"
        retrieval_note = (
            "Waiting for clarification before recommending products."
            if query.language == "en"
            else "بانتظار توضيح إضافي قبل ترشيح المنتجات."
        )
        return RecommendationResponse(
            structured_data=query,
            recommendations=[],
            retrieval_note=retrieval_note,
        )

    ranked = sorted(
        (
            (product, _score_product(product, query))
            for product in catalog
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    filtered_ranked = [item for item in ranked if item[1] > 0]
    if query.budget_aed is not None:
        filtered_ranked = [item for item in filtered_ranked if item[0].price_aed <= query.budget_aed]
    if query.age_months is not None:
        filtered_ranked = [
            item
            for item in filtered_ranked
            if item[0].age_min_months <= query.age_months <= item[0].age_max_months
        ]

    query_text = query.original_query.lower()
    filtered_ranked = [
        item
        for item in filtered_ranked
        if (
            (query.category and item[0].category == query.category)
            or any(value in item[0].tags for value in query.filters)
            or (query.age_months is not None and item[0].age_min_months <= query.age_months <= item[0].age_max_months)
            or _token_overlap_count(query_text, item[0]) > 0
        )
    ]

    if not filtered_ranked:
        query.confidence = min(query.confidence, 0.35)
        query.confidence_label = "low"
        return RecommendationResponse(
            structured_data=query,
            recommendations=[],
            refusal_message="I don't know" if query.language == "en" else "لا أعرف",
        )

    top_five = filtered_ranked[:5]
    recommendations = [
        Recommendation(
            product_id=product.id,
            product_name=product.name_ar if query.language == "ar" else product.name_en,
            why_it_fits=_why_it_fits(product, query),
            budget_suitability=_budget_note(product.price_aed, query.budget_aed, query.language),
            price_aed=product.price_aed,
            evidence=_evidence(product, query),
            score=score,
        )
        for product, score in top_five
    ]

    if len(recommendations) < 3:
        query.confidence = min(query.confidence, 0.6)
    query.confidence_label = _confidence_label(query.confidence)

    retrieval_note = (
        "Recommendations are grounded in the local product catalog and filtered by budget when provided."
        if query.language == "en"
        else "الترشيحات مستندة إلى كتالوج المنتجات المحلي وتمت تصفيتها حسب الميزانية عند توفرها."
    )
    return RecommendationResponse(
        structured_data=query,
        recommendations=recommendations,
        refusal_message=None,
        retrieval_note=retrieval_note,
    )
