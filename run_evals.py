from __future__ import annotations

import json
import sys
from pathlib import Path

from src.service import run_pipeline


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    eval_path = Path(__file__).resolve().parent / "tests" / "eval_cases.json"
    cases = json.loads(eval_path.read_text(encoding="utf-8"))

    passed = 0
    rows: list[dict[str, object]] = []
    for case in cases:
        result = run_pipeline(case["query"])
        structured = result.structured_data

        checks = {
            "intent": structured.intent == case["expected_intent"],
            "budget": case.get("expected_budget") in (None, structured.budget_aed),
            "non_empty": (len(result.recommendations) > 0) == case["expected_non_empty"],
            "refusal": (result.refusal_message is not None) == case["expect_refusal"],
            "clarification": structured.clarification_needed == case.get("expect_clarification", structured.clarification_needed),
            "grounding": all(bool(item.evidence) for item in result.recommendations),
        }

        case_passed = all(checks.values())
        if case_passed:
            passed += 1

        rows.append(
            {
                "name": case["name"],
                "passed": case_passed,
                "checks": checks,
                "intent": structured.intent,
                "budget": structured.budget_aed,
                "recommendation_count": len(result.recommendations),
                "refusal_message": result.refusal_message,
            }
        )

    summary = {
        "passed": passed,
        "total": len(cases),
        "score_percent": round((passed / len(cases)) * 100, 1),
        "results": rows,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
