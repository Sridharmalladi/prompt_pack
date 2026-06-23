"""
Core agent loop — orchestrates the conversation between the user, Claude, and the tools.

The loop is intentionally simple and framework-free: append the user message, call the
model, check stop_reason, run any requested tools, repeat. Everything is visible in this
file, which makes it easy to trace what happened on any given question.
"""

import json
from typing import Any

import anthropic

from . import config, tools

SYSTEM_PROMPT = """\
You are a marketing analytics assistant. You answer questions about campaign and channel
performance by querying a SQLite database through the tools you have been given.

A few things to keep in mind:
- If you are not sure which columns exist, call get_schema before writing any SQL.
- Always aggregate in SQL — use SUM, AVG, GROUP BY — rather than pulling raw rows and
  doing math yourself. It keeps the response fast and the context clean.
- If the question involves a metric like ROAS, CAC, or CTR, call define_metric first
  so you are working from the right formula, not a guess.
- All money figures are in USD. Be exact with numbers, say what time range you used,
  and flag any assumption you had to make.
- Finish every answer with one short sentence the marketer can actually do something
  with. Do not invent numbers.
"""


class Agent:
    def __init__(self) -> None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        # Conversation history persists across calls so follow-up questions have context.
        self.messages: list[dict[str, Any]] = []

    def ask(self, question: str, verbose: bool = False) -> str:
        self.messages.append({"role": "user", "content": question})

        # MAX_TURNS is a safety cap — well-formed questions finish in 3–4 turns.
        for _ in range(config.MAX_TURNS):
            try:
                response = self.client.messages.create(
                    model=config.MODEL,
                    max_tokens=1500,
                    system=SYSTEM_PROMPT,
                    tools=tools.TOOL_SPECS,
                    messages=self.messages,
                )
            except anthropic.APIError as e:
                return f"API error — {e}. Check your key and try again."

            self.messages.append({"role": "assistant", "content": response.content})

            # If the model didn't ask for a tool, it's done — return the final answer.
            if response.stop_reason != "tool_use":
                return _text_of(response.content)

            # Run every tool the model requested and collect the results.
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if verbose:
                    print(f"  [tool] {block.name}({json.dumps(block.input)})")
                result = tools.run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

            self.messages.append({"role": "user", "content": tool_results})

        return "I ran out of steps before finishing — try asking something more specific."


def _text_of(content: list[Any]) -> str:
    """Extract plain text from the model's response content blocks."""
    return "\n".join(b.text for b in content if getattr(b, "type", None) == "text").strip()
