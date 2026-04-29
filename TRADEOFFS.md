# Tradeoffs

## Why This Problem

I chose multilingual gift discovery because it is close to real e-commerce value:

- shoppers often describe needs in natural language, not category filters
- gifting is a high-intent, high-conversion use case
- the problem benefits from structured extraction plus retrieval, not just a UI tweak
- it matters in both English and Arabic

I rejected broader product search because it was too wide for the timebox. I also rejected customer-support triage because it needs more policy design and higher-stakes evaluation.

## Model and Architecture Choice

The prototype uses a dual-path extraction design:

- default: deterministic extractor so the project runs without any paid dependency
- optional: OpenRouter for better semantic extraction into the same schema

This is a deliberate tradeoff:

- better reproducibility and easy setup
- lower semantic quality than a stronger always-on LLM system

The recommender is retrieval-based over a synthetic local catalog rather than a generative model inventing products. That keeps outputs grounded and makes "I don't know" feasible.

## Uncertainty Handling

The system avoids false confidence in three ways:

1. Vague queries trigger `clarification_needed`
2. Unsafe medical queries are refused
3. If no product receives a useful score, the system returns `I don't know`

This is more production-safe than forcing a recommendation for every input.

## What Was Cut

To stay inside a realistic intern-project timebox, I did not build:

- live catalog ingestion from a commerce backend
- embeddings-based retrieval
- native-quality EN and AR copy generation for each recommendation
- user feedback loops
- reranking by conversion or popularity signals
- a full API backend and database

## Known Failure Modes

- Arabic extraction still depends on limited heuristics unless OpenRouter is enabled
- the catalog is synthetic and small, so retrieval quality is not representative of a live store
- category detection is still rule-based in fallback mode, so unusual phrasing can map to a generic search
- recommendation quality depends heavily on tag quality because retrieval is lexical and metadata-driven, not embeddings-based

## What I Would Build Next

If I had another 5 to 10 hours, I would add:

- embedding retrieval over a larger messy catalog
- bilingual generation tuned separately for English and Arabic output quality
- product citations and feature highlights pulled from source attributes
- click feedback logging and offline ranking evaluation
- a better evaluator for recommendation relevance, not just extraction correctness

## Why This Is Still A Good Submission

Even though the prototype is intentionally scoped down, it hits the core signals in the brief:

- real e-commerce use case
- non-trivial AI engineering
- multilingual support
- structured validated output
- explicit uncertainty behavior
- grounded evidence for every recommendation
- runnable demo plus documented evals and tradeoffs
