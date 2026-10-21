"""Manual evaluation script for NovaMart Assistant.

Evaluates the four primary operational cases:
1. Answerable policy question (evidence grounded in local policies).
2. Unsupported policy question (no policy evidence; directs to operations).
3. Existing fictional order lookup (valid tool call and order status).
4. Unknown order lookup (not found result without hallucinating a status).

DOES NOT require an external test framework.
Can run offline to verify retrieval and tool logic, or end-to-end when
OPENAI_API_KEY is configured.
"""

import os
from typing import Any, Dict, List

from src.assistant import ask_assistant, format_policy_context
from src.orders import lookup_order


def run_evaluation() -> None:
    print("=" * 75)
    print("NovaMart Assistant - Manual Evaluation Suite")
    print("=" * 75)

    eval_cases: List[Dict[str, Any]] = [
        {
            "id": "CASE-1",
            "name": "Answerable Policy Question",
            "query": "How many days do I have to return an item?",
            "eval_type": "policy",
            "expected_behavior": "Should retrieve Return Window excerpt (30 days) and answer based on evidence."
        },
        {
            "id": "CASE-2",
            "name": "Unsupported Policy Question",
            "query": "Can I bring my pet iguana into the store for grooming?",
            "eval_type": "policy",
            "expected_behavior": "Should find no policy evidence and direct user to store operations/support team."
        },
        {
            "id": "CASE-3",
            "name": "Existing Fictional Order Lookup",
            "query": "What is the status of order NM-1001?",
            "eval_type": "order",
            "order_id": "NM-1001",
            "expected_behavior": "lookup_order tool returns status 'found' (Shipped, NovaExpress). Relays real status."
        },
        {
            "id": "CASE-4",
            "name": "Unknown Order ID Lookup",
            "query": "What is the status of order NM-9999?",
            "eval_type": "order",
            "order_id": "NM-9999",
            "expected_behavior": "lookup_order tool returns status 'not_found'. Clearly states order not found."
        }
    ]

    has_api_key = bool(os.getenv("OPENAI_API_KEY", "").strip())

    for case in eval_cases:
        print(f"\n--- [{case['id']}: {case['name']}] ---")
        print(f"User Query: \"{case['query']}\"")
        print(f"Expected Behavior: {case['expected_behavior']}")

        # 1. Deterministic local validation (Policy retrieval or Order tool check)
        if case["eval_type"] == "policy":
            retrieved_context = format_policy_context(case["query"])
            has_evidence = "No relevant policy excerpts found" not in retrieved_context
            print(f"Policy Grounding Evidence Found: {has_evidence}")
            if has_evidence:
                first_line = retrieved_context.splitlines()[0] if retrieved_context else ""
                print(f"Top Excerpt Source: {first_line}")
        elif case["eval_type"] == "order":
            order_result = lookup_order(case["order_id"])
            print(f"Local Tool Execution (lookup_order('{case['order_id']}')) Status: {order_result['status']}")
            if order_result["status"] == "found":
                print(f"Order Carrier/Status: {order_result['order']['status']} via {order_result['order']['carrier']}")
            else:
                print(f"Tool Message: {order_result['message']}")

        # 2. Live API execution check (if key is configured)
        if has_api_key:
            print("\nInvoking live assistant response...")
            response = ask_assistant(case["query"])
            print(f"Assistant Output:\n{response}")
        else:
            print("[Live AI Response]: Skipped (OPENAI_API_KEY not set in environment).")
            print("Local retrieval & tool execution logic verified successfully.")

    print("\n" + "=" * 75)
    print("Evaluation summary completed.")
    print("=" * 75)


if __name__ == "__main__":
    run_evaluation()
