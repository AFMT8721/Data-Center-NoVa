import json
import urllib.error

import pytest

from src.scoring import intent


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("What will my monthly power bill be?", "bill_prediction"),
        ("Show Dominion's historical residential rates", "bill_context"),
        ("What does the county AQI monitor show?", "air_quality"),
        ("How many diesel generators does the permit allow?", "air_permit"),
        ("Compare bill and air evidence", "both"),
        ("What should residents know about this data center?", "both"),
        ("Hello!", "greeting"),
        ("What can you do?", "capabilities"),
        ("Hi, what does the AQI map show?", "air_quality"),
    ],
)
def test_keyword_intent(query: str, expected: str) -> None:
    assert intent.keyword_intent(query) == expected


def test_parse_structured_intent() -> None:
    body = {"response": json.dumps({"intent": "air_permit"})}
    assert intent._parse_intent(body) == "air_permit"


def test_parse_rejects_unknown_intent() -> None:
    body = {"response": json.dumps({"intent": "write_a_poem"})}
    assert intent._parse_intent(body) is None


def test_classifier_uses_structured_output(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"response": json.dumps({"intent": "bill_context"})}
            ).encode()

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(intent.urllib.request, "urlopen", fake_urlopen)
    assert intent.classify_intent("Show utility rates") == "bill_context"
    assert captured["timeout"] == intent.OLLAMA_TIMEOUT_SECONDS
    assert captured["payload"]["format"]["properties"]["intent"]["enum"] == sorted(
        intent.INTENTS
    )


def test_classifier_failure_returns_none(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(intent.urllib.request, "urlopen", fail)
    assert intent.classify_intent("What is the AQI?") is None
