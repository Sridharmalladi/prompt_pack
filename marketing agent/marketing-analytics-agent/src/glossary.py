"""
Metric glossary — business definitions for the marketing terms the agent works with.

The lookup() interface is shaped to mirror what a vector store would expose, so the
keyword-overlap implementation can be swapped for dense embeddings (pgvector, Pinecone)
without changing anything else in the codebase.
"""

import re

GLOSSARY: dict[str, str] = {
    "ROAS":            "Return on Ad Spend = revenue / spend. A ROAS of 4 means $4 of "
                       "revenue for every $1 spent. Higher is better.",
    "CAC":             "Customer Acquisition Cost = spend / conversions. Average cost "
                       "to acquire one converting customer.",
    "CTR":             "Click-Through Rate = clicks / impressions. How good an ad is at "
                       "earning a click.",
    "CVR":             "Conversion Rate = conversions / clicks. Share of clicks that become "
                       "a conversion.",
    "CPC":             "Cost Per Click = spend / clicks. Average price paid per click.",
    "AOV":             "Average Order Value = revenue / conversions. Average revenue per order.",
    "incrementality":  "The portion of conversions genuinely caused by a campaign "
                       "vs. those that would have happened anyway. Measured with holdout or "
                       "geo experiments, not last-click attribution.",
}

_STOPWORDS = {
    "the", "and", "for", "that", "with", "would", "have", "this", "are",
    "how", "what", "per", "one", "not", "you", "your", "from", "than",
}


def _tokens(text: str) -> set[str]:
    """Return meaningful lowercase tokens from text, filtering short words and stopwords."""
    return {
        t for t in re.findall(r"[a-z]+", text.lower())
        if len(t) >= 3 and t not in _STOPWORDS
    }


def lookup(query: str, k: int = 3) -> list[str]:
    """Return up to k glossary entries most relevant to the query.

    Relevance is scored by token overlap between the query and each term + definition.
    Exact acronym matches receive a score boost so "what is ROAS?" reliably surfaces
    the ROAS entry even if the surrounding words don't overlap with the definition.
    """
    q_tokens = _tokens(query)
    scored = []
    for term, definition in GLOSSARY.items():
        score = len(q_tokens & _tokens(term + " " + definition))
        if term.lower() in query.lower():
            score += 5  # exact acronym in the query is a strong signal
        if score:
            scored.append((score, f"{term}: {definition}"))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [text for _, text in scored[:k]]
