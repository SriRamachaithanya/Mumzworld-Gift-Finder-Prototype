# 3-Minute Loom Script

## Goal

Record a short walkthrough that shows:

- the product working end to end
- one bilingual example
- one vague query that triggers clarification
- one unsafe query that triggers refusal
- the project is grounded and evaluated, not just prompted

## Before Recording

1. Run:

```bash
streamlit run app.py
```

2. Keep `README.md` open in another tab.
3. Have `python run_evals.py` ready in the terminal if you want to show the eval result quickly.

## Suggested Script

### 0:00 - 0:20 Intro

"I built a multilingual gift finder for a Mumzworld-style e-commerce catalog. The system accepts natural-language requests in English or Arabic, extracts structured shopping intent, retrieves grounded products from a catalog, and returns explainable recommendations with evidence. It also asks for clarification on vague inputs and refuses unsafe medical-style queries."

### 0:20 - 0:55 English gift query

Paste:

`Thoughtful gift for a friend with a 6-month-old under 200 AED`

Say:

"Here the system extracts the intent as gift, identifies the age and budget, and only returns products within budget. Each recommendation includes why it fits and evidence showing which catalog attributes matched."

Scroll through:

- structured JSON
- confidence
- recommendations
- evidence
- strict output section

### 0:55 - 1:20 Arabic query

Paste:

`أريد هدية عملية لأم جديدة أقل من 250 درهم`

Say:

"This shows the bilingual behavior. The input is in Arabic, the extraction still becomes structured, and the recommendation text is shown in Arabic rather than as a literal English-first workflow."

### 1:20 - 1:45 Clarification example

Paste:

`Need something nice`

Say:

"For vague requests, I did not want the system to act confident and guess. Instead, it pauses and asks a follow-up question before recommending anything."

Point to:

- `clarification_needed`
- warning message
- no recommendations returned

### 1:45 - 2:10 Medical refusal example

Paste:

`My baby has fever and rash, what should I buy?`

Say:

"This is an unsafe use case for a commerce assistant. Instead of hallucinating products or advice, the system refuses and directs the user to consult a doctor."

### 2:10 - 2:35 Grounding and architecture

Open `README.md` and say:

"The key design choice was grounding. Recommendations are pulled from a local product catalog rather than generated from scratch. The pipeline combines structured extraction, schema validation, metadata-based retrieval, and explicit uncertainty handling."

### 2:35 - 2:55 Evals

Show the terminal output from:

```bash
python run_evals.py
```

Say:

"I included 12 evaluation cases covering English and Arabic requests, budget-sensitive retrieval, vague inputs, and medical refusal behavior. The current local run passes all 12."

### 2:55 - 3:00 Close

"If I extended this further, I would replace the lexical retrieval with embeddings over a larger catalog and improve native-quality Arabic generation, but this version is intentionally scoped to be runnable, grounded, and honestly evaluated."

## Tips

- Keep the recording under 3 minutes by moving quickly between examples.
- Do not spend too long on the code.
- Emphasize tradeoffs and safety, not just features.
- If the UI feels slow, pre-open the app before starting the recording.
