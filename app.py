from __future__ import annotations

import streamlit as st

from src.service import render_text_response, run_pipeline


st.set_page_config(page_title="Mumzworld Gift Finder", page_icon="🎁", layout="centered")

st.title("Mumzworld Gift Finder Prototype")
st.caption("AI-powered bilingual discovery and gift recommendation engine.")

examples = [
    "Thoughtful gift for a friend with a 6-month-old under 200 AED",
    "Travel-friendly gift for a new mom under 300 AED",
    "أريد هدية عملية لأم جديدة أقل من 250 درهم",
    "Organic newborn gift",
    "My baby has fever and rash, what should I buy?",
]

selected_example = st.selectbox("Quick examples", [""] + examples)
default_query = selected_example or ""
user_query = st.text_area("User query", value=default_query, height=120, placeholder="Describe what the mom needs in English or Arabic...")

if st.button("Get Recommendations", type="primary", disabled=not user_query.strip()):
    result = run_pipeline(user_query.strip())
    is_arabic = result.structured_data.language == "ar"
    confidence_label = result.structured_data.confidence_label

    st.subheader("Structured Data")
    st.json(result.structured_data.model_dump())
    st.caption(
        f"Extraction confidence: {confidence_label} ({result.structured_data.confidence:.2f})"
        if not is_arabic
        else f"مستوى الثقة في الاستخراج: {confidence_label} ({result.structured_data.confidence:.2f})"
    )

    if result.structured_data.clarification_needed and result.structured_data.clarification_question:
        st.warning(result.structured_data.clarification_question)

    if result.retrieval_note:
        st.info(result.retrieval_note)

    if result.refusal_message:
        st.error(result.refusal_message)
    elif result.recommendations:
        st.subheader("Recommendations")
        for index, recommendation in enumerate(result.recommendations, start=1):
            with st.container(border=True):
                st.markdown(f"**{index}. {recommendation.product_name}**")
                st.write(recommendation.why_it_fits)
                st.caption(f"Price: {recommendation.price_aed} AED" if not is_arabic else f"السعر: {recommendation.price_aed} درهم")
                st.caption(recommendation.budget_suitability)
                st.caption("Evidence: " + " | ".join(recommendation.evidence) if not is_arabic else "الأدلة: " + " | ".join(recommendation.evidence))
                st.caption(f"Score: {recommendation.score}")

    st.subheader("Strict Output Format")
    st.code(render_text_response(result), language="text")

st.divider()
st.markdown(
    """
    ### Notes
    - Uses a small local product catalog for grounded retrieval.
    - If `OPENROUTER_API_KEY` is set, query extraction can use OpenRouter; otherwise a deterministic parser is used.
    - Medical queries trigger a refusal instead of a product answer.
    - Vague queries now pause for clarification instead of pretending certainty.
    """
)
