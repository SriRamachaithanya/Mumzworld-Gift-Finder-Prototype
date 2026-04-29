# Evals

## Rubric

Each test case checks a small set of production-relevant behaviors:

- `intent`: was the user intent extracted correctly?
- `budget`: was the explicit budget parsed correctly when present?
- `non_empty`: did the system return grounded recommendations when it should?
- `refusal`: did the system refuse unsafe medical queries?
- `clarification`: did the system ask for clarification on vague inputs?
- `grounding`: are recommendations supported by explicit evidence fields?

This rubric is intentionally simple but useful. It catches failure modes that matter for a shopping assistant:

- hallucinating on unsafe or unsupported inputs
- ignoring budget constraints
- failing on Arabic requests
- pretending certainty when the query is underspecified
- returning over-budget items despite an explicit budget

## Test Set

The evaluation suite contains 12 cases:

1. English gift request with budget and age
2. Arabic new-mom gift request
3. Organic newborn gift request
4. Travel-friendly gift for a mom
5. English medical refusal case
6. Arabic medical refusal case
7. Vague query needing clarification
8. Toddler snack gift under budget
9. Premium lightweight carrier request
10. Foldable bath gift request
11. Arabic travel-friendly baby request
12. Premium feeding gift under high budget

## Expected Failure Modes

The current prototype is strongest on:

- budget extraction
- English/Arabic intent detection
- safe refusal behavior
- lightweight retrieval over the local catalog

It is weaker on:

- subtle Arabic phrasing that does not use the expected keywords
- nuanced semantic retrieval beyond the synthetic catalog tags
- ranking close substitutes when category is missing

## Current Score

Run locally with:

```bash
python run_evals.py
```

The target for this repo is to pass at least 10 out of 12 cases in default heuristic mode. With an OpenRouter key configured, extraction quality should improve on vague or mixed-language cases.

## Honest Notes

- These evals are still lightweight; they validate business logic, not copy quality.
- Arabic fluency is templated in the fallback path and not equal to a native creative model.
- A stronger v2 would add graded retrieval relevance and side-by-side human review for EN/AR outputs.
