import json

from app.analyzers.ai_analyzer import AIAnalyzer


def test_ai_analyzer_disabled_by_default(monkeypatch):
    monkeypatch.setattr("app.config.settings.AI_INTEGRATIONS_ENABLED", False)

    analyzer = AIAnalyzer()
    result = analyzer.analyze("sample.py", "print('hello')\n")

    assert result.analyzer_name == "ai_review"
    assert result.score == 10.0
    assert result.issues == []


def test_ai_analyzer_parses_provider_response(monkeypatch):
    monkeypatch.setattr("app.config.settings.AI_INTEGRATIONS_ENABLED", True)
    monkeypatch.setattr("app.config.settings.AI_PROVIDERS", ["coderabbit"])
    monkeypatch.setattr("app.config.settings.AI_CODERABBIT_API_URL", "https://example.test/review")
    monkeypatch.setattr("app.config.settings.AI_CODERABBIT_API_KEY", "token")

    class _DummyResponse:
        def __init__(self, payload: dict):
            self._payload = payload

        def read(self):
            return json.dumps(self._payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(req, timeout=0):
        payload = {
            "score": 7.5,
            "summary": "1 finding",
            "issues": [
                {
                    "severity": "high",
                    "message": "Potential injection risk",
                    "file": "main.rs",
                    "line": 12,
                    "rule": "injection_risk",
                }
            ],
        }
        return _DummyResponse(payload)

    monkeypatch.setattr("app.analyzers.ai_analyzer.request.urlopen", _fake_urlopen)

    analyzer = AIAnalyzer()
    result = analyzer.analyze("main.rs", "fn main() {}")

    assert result.score == 7.5
    assert len(result.issues) == 1
    assert result.issues[0].severity == "error"
    assert result.issues[0].rule == "injection_risk"


def test_ai_analyzer_openrouter_uses_selected_model(monkeypatch):
    monkeypatch.setattr("app.config.settings.AI_INTEGRATIONS_ENABLED", True)
    monkeypatch.setattr("app.config.settings.AI_PROVIDERS", ["openrouter"])
    monkeypatch.setattr(
        "app.config.settings.AI_OPENROUTER_API_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    )
    monkeypatch.setattr("app.config.settings.AI_OPENROUTER_API_KEY", "token")
    monkeypatch.setattr(
        "app.config.settings.AI_OPENROUTER_MODEL",
        "z-ai/glm-4.5-air:free",
    )
    # selected_model must also be in AI_OPENROUTER_FREE_MODELS to be used as primary
    monkeypatch.setattr(
        "app.config.settings.AI_OPENROUTER_FREE_MODELS",
        ["stepfun/step-3.5-flash:free", "z-ai/glm-4.5-air:free"],
    )

    captured_request = {"body": None}

    class _DummyResponse:
        def read(self):
            payload = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "openrouter ok",
                                    "score": 8.2,
                                    "issues": [
                                        {
                                            "severity": "warning",
                                            "message": "Unsafe block needs review",
                                            "file": "main.rs",
                                            "line": 7,
                                            "rule": "unsafe_block_review",
                                        }
                                    ],
                                }
                            )
                        }
                    }
                ]
            }
            return json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(req, timeout=0):
        captured_request["body"] = req.data.decode("utf-8")
        return _DummyResponse()

    monkeypatch.setattr("app.analyzers.ai_analyzer.request.urlopen", _fake_urlopen)

    analyzer = AIAnalyzer(selected_model="stepfun/step-3.5-flash:free")
    result = analyzer.analyze("main.rs", "fn main() { unsafe { println!(\"x\"); } }")

    assert captured_request["body"] is not None
    sent_body = json.loads(captured_request["body"])
    assert sent_body["model"] == "stepfun/step-3.5-flash:free"
    assert result.score == 8.2
    assert len(result.issues) == 1
    assert result.issues[0].rule == "unsafe_block_review"


def test_ai_analyzer_openrouter_missing_key_skips_provider(monkeypatch):
    monkeypatch.setattr("app.config.settings.AI_INTEGRATIONS_ENABLED", True)
    monkeypatch.setattr("app.config.settings.AI_PROVIDERS", ["openrouter"])
    monkeypatch.setattr("app.config.settings.AI_OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    monkeypatch.setattr("app.config.settings.AI_OPENROUTER_API_KEY", "")

    analyzer = AIAnalyzer()
    result = analyzer.analyze("main.rs", "fn main() {}")

    assert result.analyzer_name == "ai_review"
    assert result.score == 10.0
    assert result.issues == []
    assert "missing api key" not in result.summary.lower()
