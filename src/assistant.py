"""Terminal assistant for NovaMart associates.

Integrates local policy search grounding and a fictional order lookup tool
using OpenAI's Python SDK for tool/function calling.

ALL DATA AND POLICIES ARE FICTIONAL AND DESIGNED FOR PORTFOLIO DEMONSTRATION.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

from src import config
from src.orders import lookup_order
from src.search import search_policies

# Tool schema definition following OpenAI's function calling specification
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up status and details for a fictional NovaMart customer order by its order ID (e.g., 'NM-1001').",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The customer order identifier to look up, e.g., 'NM-1001'."
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]

SYSTEM_PROMPT_TEMPLATE = """You are the internal assistant for NovaMart, a fictional omnichannel retail chain.
Your role is to assist store staff, customer service representatives, and operations teams with policy questions and order lookups.

STRICT OPERATIONAL GUIDELINES:
1. Policy Questions:
   - Rely ONLY on the provided policy excerpts below.
   - If no relevant policy excerpts are provided, or if the provided excerpts do not establish the answer, you MUST state that you could not find support in the available NovaMart policies and direct the user to the NovaMart operations team (support@novamart-example.com or the store Duty Manager).
   - You MUST NOT invent, guess, or extrapolate policy details.
2. Order Status Inquiries:
   - When the user asks about an order, you MUST call the `lookup_order` tool with the requested order ID.
   - Do NOT invent or assume an order status.
   - If the tool reports that the order was not found, inform the user clearly that the order ID was not found in NovaMart's records.
3. Fictional Nature & Safety:
   - All orders and policies are fictional.
   - Never reveal, ask for, or print API keys, credentials, or real personal data.
   - Keep answers clear, professional, and concise.

AVAILABLE LOCAL POLICY EXCERPTS:
{policy_context}
"""


def format_policy_context(query: str) -> str:
    """Retrieve and format excerpts from the local policy knowledge base."""
    excerpts = search_policies(query, top_k=2)
    if not excerpts:
        return "No relevant policy excerpts found in NovaMart's local policies for this query."

    formatted = []
    for idx, item in enumerate(excerpts, 1):
        formatted.append(
            f"--- Excerpt {idx} (Source: {item['source']} | Section: {item['section']}) ---\n"
            f"{item['excerpt']}\n"
        )
    return "\n".join(formatted)


def ask_assistant(user_message: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Process a user query through the NovaMart Assistant pipeline.
    
    1. Checks for API key and SDK availability.
    2. Retrieves grounded policy excerpts from local documents.
    3. Sends messages to OpenAI Chat Completions API with the lookup_order tool.
    4. Handles and validates any tool calls in Python code.
    5. Returns the final assistant response or a safe error message.
    """
    # 1. Validate API Key presence without exposing secrets
    api_key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        return (
            "Configuration Notice: The OPENAI_API_KEY environment variable is not set.\n"
            "To use the assistant with live AI responses, set your key in your environment:\n"
            "  export OPENAI_API_KEY='your_api_key_here'\n"
            "Do not commit API keys or share real credentials."
        )

    # 2. Check for OpenAI SDK installation
    try:
        from openai import OpenAI, OpenAIError
    except ModuleNotFoundError:
        return (
            "Setup Notice: The 'openai' Python package is not installed.\n"
            "Please install project dependencies by running:\n"
            "  pip install -r requirements.txt"
        )

    # 3. Ground with local policy search excerpts
    policy_context = format_policy_context(user_message)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(policy_context=policy_context)

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # 4. Invoke OpenAI Chat Completions with error handling
    try:
        client = OpenAI(api_key=api_key)
        model = config.OPENAI_MODEL

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
    except OpenAIError as err:
        # Safe error reporting that never prints the API key or raw auth headers
        return f"OpenAI API Error: {type(err).__name__}. Please verify network connectivity and API key permissions."
    except Exception as err:
        return f"Unexpected Error: Unable to complete assistant request ({type(err).__name__})."

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 5. Handle tool call if requested by model
    if tool_calls:
        # Append assistant message with tool calls to conversation history
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name

            if function_name == "lookup_order":
                # Parse and validate tool arguments safely
                try:
                    args = json.loads(tool_call.function.arguments)
                    order_id = args.get("order_id", "")
                except (json.JSONDecodeError, AttributeError):
                    tool_result = {
                        "status": "error",
                        "message": "Malformed arguments passed to lookup_order."
                    }
                else:
                    tool_result = lookup_order(str(order_id))

                # Append tool response
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_result)
                })
            else:
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"status": "error", "message": f"Unknown tool '{function_name}'."})
                })

        # Second API call: let the model formulate the final response using the tool output
        try:
            second_response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            return second_response.choices[0].message.content or "No response received."
        except OpenAIError as err:
            return f"OpenAI API Error following tool execution: {type(err).__name__}."
        except Exception as err:
            return f"Unexpected Error following tool execution: {type(err).__name__}."

    return response_message.content or "No response received."


def interactive_session() -> None:
    """Run an interactive terminal session for NovaMart Assistant."""
    print("=" * 70)
    print("NovaMart Assistant - Terminal Interface (Fictional Portfolio Demo)")
    print("=" * 70)
    print("Type your questions about store policies or order lookups (e.g. 'NM-1001').")
    print("Type 'exit' or 'quit' to end the session.\n")

    history: List[Dict[str, str]] = []

    while True:
        try:
            user_input = input("User: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Session ended. Goodbye!")
            break

        print("\nThinking...")
        reply = ask_assistant(user_input, history=history)
        print(f"\nAssistant:\n{reply}\n")
        print("-" * 70)

        # Keep a brief conversational memory for context
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": reply})
        if len(history) > 6:
            history = history[-6:]


if __name__ == "__main__":
    interactive_session()
