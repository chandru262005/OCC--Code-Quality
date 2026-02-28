#!/usr/bin/env python3
"""Quick diagnostics for OpenRouter AI integration.

Checks local config and can optionally run a tiny API probe to surface
HTTP 401/402/429 issues early.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib import error, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings  # noqa: E402

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


def _mask_secret(secret: str) -> str:
    if not secret:
        return "(empty)"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


def _print_result(level: str, message: str) -> None:
    icon = {PASS: "✅", WARN: "⚠️", FAIL: "❌"}.get(level, "•")
    print(f"{icon} [{level}] {message}")


def _build_probe_payload(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "temperature": 0,
        "max_tokens": 60,
        "messages": [
            {
                "role": "user",
                "content": "Return strict JSON only: {\"ok\": true}",
            }
        ],
    }


def _probe_openrouter(model: str, timeout_seconds: int) -> tuple[str, str]:
    payload = _build_probe_payload(model)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AI_OPENROUTER_API_KEY}",
    }

    if settings.AI_OPENROUTER_HTTP_REFERER:
        headers["HTTP-Referer"] = settings.AI_OPENROUTER_HTTP_REFERER
    if settings.AI_OPENROUTER_APP_TITLE:
        headers["X-OpenRouter-Title"] = settings.AI_OPENROUTER_APP_TITLE

    req = request.Request(
        url=settings.AI_OPENROUTER_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return WARN, "Probe succeeded but response was not JSON"

            choices = data.get("choices") if isinstance(data, dict) else None
            if isinstance(choices, list) and choices:
                return PASS, f"Probe succeeded with model '{model}'"
            return WARN, "Probe returned JSON but no choices were found"

    except error.HTTPError as exc:
        if exc.code == 401:
            return FAIL, "HTTP 401 Unauthorized: API key is invalid"
        if exc.code == 402:
            return FAIL, "HTTP 402 Payment Required: no balance/quota"
        if exc.code == 429:
            return FAIL, "HTTP 429 Too Many Requests: rate-limited or free-tier exhausted"
        return FAIL, f"HTTP {exc.code} from OpenRouter"
    except Exception as exc:  # pylint: disable=broad-except
        return FAIL, f"Probe failed: {exc}"


def _probe_fallback_models(selected_model: str, timeout_seconds: int) -> tuple[bool, list[str]]:
    """Try alternate free models and return whether any probe succeeds."""
    candidates = [m.strip() for m in settings.AI_OPENROUTER_FREE_MODELS if m.strip() and m.strip() != selected_model]
    if not candidates:
        return False, []

    any_success = False
    messages: list[str] = []
    for model in candidates:
        level, message = _probe_openrouter(model, timeout_seconds)
        messages.append(f"{model}: [{level}] {message}")
        if level == PASS:
            any_success = True
            break

    return any_success, messages


def run_checks(probe: bool, timeout_seconds: int) -> int:
    print("OpenRouter Integration Diagnostics")
    print("=" * 34)

    failures = 0

    if settings.AI_INTEGRATIONS_ENABLED:
        _print_result(PASS, "AI integrations are enabled")
    else:
        _print_result(WARN, "AI integrations are disabled (AI_INTEGRATIONS_ENABLED=false)")

    providers = [p.strip().lower() for p in settings.AI_PROVIDERS]
    if "openrouter" in providers:
        _print_result(PASS, "openrouter is included in AI_PROVIDERS")
    else:
        _print_result(WARN, "openrouter is not included in AI_PROVIDERS")

    if settings.AI_OPENROUTER_API_URL.startswith("https://"):
        _print_result(PASS, f"API URL looks valid: {settings.AI_OPENROUTER_API_URL}")
    else:
        _print_result(FAIL, f"API URL must be https: {settings.AI_OPENROUTER_API_URL}")
        failures += 1

    if settings.AI_OPENROUTER_API_KEY.strip():
        _print_result(PASS, f"API key is configured: {_mask_secret(settings.AI_OPENROUTER_API_KEY.strip())}")
    else:
        _print_result(FAIL, "AI_OPENROUTER_API_KEY is empty")
        failures += 1

    selected_model = settings.AI_OPENROUTER_MODEL.strip()
    free_models = [m.strip() for m in settings.AI_OPENROUTER_FREE_MODELS if m.strip()]

    if selected_model:
        _print_result(PASS, f"Selected model: {selected_model}")
    else:
        _print_result(FAIL, "AI_OPENROUTER_MODEL is empty")
        failures += 1

    if free_models:
        if selected_model in free_models:
            _print_result(PASS, "Selected model exists in AI_OPENROUTER_FREE_MODELS")
        else:
            _print_result(
                WARN,
                "Selected model is not in AI_OPENROUTER_FREE_MODELS (fallback may choose another model)",
            )
    else:
        _print_result(WARN, "AI_OPENROUTER_FREE_MODELS is empty")

    if settings.AI_MAX_FILES <= 30:
        _print_result(PASS, f"AI_MAX_FILES={settings.AI_MAX_FILES} (good for rate limits)")
    else:
        _print_result(WARN, f"AI_MAX_FILES={settings.AI_MAX_FILES} is high (consider <= 30)")

    if settings.AI_MAX_CHARS_PER_FILE <= 20000:
        _print_result(PASS, f"AI_MAX_CHARS_PER_FILE={settings.AI_MAX_CHARS_PER_FILE} (good default)")
    else:
        _print_result(
            WARN,
            f"AI_MAX_CHARS_PER_FILE={settings.AI_MAX_CHARS_PER_FILE} is high (consider <= 20000)",
        )

    if probe:
        if failures > 0:
            _print_result(WARN, "Skipping live probe until failures above are fixed")
        else:
            level, message = _probe_openrouter(selected_model, timeout_seconds)
            _print_result(level, message)
            if level == FAIL:
                recovered, fallback_messages = _probe_fallback_models(selected_model, timeout_seconds)
                for msg in fallback_messages:
                    print(f"   ↳ {msg}")

                if recovered:
                    _print_result(WARN, "Selected model failed, but a fallback free model works")
                else:
                    failures += 1
    else:
        _print_result(WARN, "Live API probe skipped (use --probe to test network/quota)")

    print("=" * 34)
    if failures:
        print(f"Completed with {failures} blocking issue(s).")
        return 1

    print("Completed with no blocking issues.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenRouter configuration and optional connectivity")
    parser.add_argument("--probe", action="store_true", help="Perform a small live API probe")
    parser.add_argument("--timeout", type=int, default=20, help="Probe timeout in seconds")
    args = parser.parse_args()

    return run_checks(probe=args.probe, timeout_seconds=max(1, args.timeout))


if __name__ == "__main__":
    sys.exit(main())
