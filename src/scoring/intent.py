"""Optional local-LLM query-domain classification.

Calls a local Ollama instance to classify a resident's question as "bill",
"air", or "both" -- routing only. The model never generates any part of the
answer text; that stays template-based and contract-enforced in reply.py.
Any failure (Ollama not running, timeout, unparseable output) returns None
so the caller falls back to the deterministic keyword router.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT_SECONDS = 3.0

CLASSIFY_PROMPT = """You classify a Northern Virginia resident's question about a proposed \
data center into exactly one label. Reply with only the label, nothing else.

Labels:
- bill: about electricity cost, rates, or utility bills
- air: about air quality, emissions, generators, or AQI
- both: touches both bill and air topics, or the question is general/unclear

Question: {query}
Label:"""


def classify_domain(query: str) -> str | None:
    """Return "bill", "air", or "both", or None if the local model is
    unavailable or its output can't be parsed as one of those labels."""
    payload = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": CLASSIFY_PROMPT.format(query=query),
            "stream": False,
            "options": {"temperature": 0},
        }
    ).encode()
    request = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    label = str(body.get("response", "")).strip().lower().strip(".")
    return label if label in {"bill", "air", "both"} else None
