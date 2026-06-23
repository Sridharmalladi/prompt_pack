"""
Command-line interface — interactive chat or one-shot mode.

Usage
-----
python -m src.cli                      # interactive session
python -m src.cli --verbose            # interactive, prints each tool call
python -m src.cli "your question"      # one-shot, prints answer and exits
python -m src.cli --verbose "question" # one-shot with tool call trace
"""

import sys

from . import config
from .agent import Agent

BANNER = """\
Marketing Analytics Agent
Ask about campaign or channel performance. Type 'exit' to quit.

Try:
  Which channel had the best ROAS over the last 90 days?
  How did Spring Sale spend trend week over week?
  What's our blended CAC, and which campaign is the most expensive?
"""


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--verbose"]
    verbose = "--verbose" in sys.argv

    try:
        agent = Agent()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # One-shot mode: question passed as a CLI argument.
    if args:
        print(agent.ask(" ".join(args), verbose=verbose))
        return

    # Interactive mode: read questions in a loop until the user exits.
    print(BANNER)
    print(f"(model: {config.MODEL})\n")
    while True:
        try:
            question = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue
        print("\nagent > " + agent.ask(question, verbose=verbose) + "\n")


if __name__ == "__main__":
    main()
