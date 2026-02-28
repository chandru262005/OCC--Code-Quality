from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib import error, request

from app.analyzers.base import BaseAnalyzer
from app.config import settings
from app.models.report import AnalyzerResult, Issue


class AIAnalyzer(BaseAnalyzer):
    """Optional external AI review analyzer.

    This analyzer supports provider adapters configured via environment variables.
    It is disabled by default and will only run when explicitly enabled.
    """

    @property
    def name(self) -> str:
        return "ai_review"

    def analyze(self, file_path: str, source_code: str | None = None) -> AnalyzerResult:
        if source_code is None:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()
        return self.analyze_multiple({file_path: source_code})

    def analyze_multiple(self, files: dict[str, str]) -> AnalyzerResult:
        if not settings.AI_INTEGRATIONS_ENABLED:
            return AnalyzerResult(
                analyzer_name=self.name,
                score=10.0,
                issues=[],
                summary="ai_review: disabled",
            )

        providers = self._configured_providers()
        if not providers:
            return AnalyzerResult(
                analyzer_name=self.name,
                score=10.0,
                issues=[],
                summary="ai_review: enabled but no provider endpoints configured",
            )

        selected_items = list(files.items())[: settings.AI_MAX_FILES]
        files_payload = [
            {
                "file_path": path,
                "language": self._detect_language(path),
                "content": code[: settings.AI_MAX_CHARS_PER_FILE],
                "truncated": len(code) > settings.AI_MAX_CHARS_PER_FILE,
            }
            for path, code in selected_items
        ]

        all_issues: list[Issue] = []
        provider_scores: list[float] = []
        provider_summaries: list[str] = []

        for provider_name, conf in providers.items():
            issues, score, summary = self._call_provider(
                provider_name=provider_name,
                url=conf["url"],
                api_key=conf["api_key"],
                files_payload=files_payload,
            )
            all_issues.extend(issues)
            if score is not None:
                provider_scores.append(score)
            provider_summaries.append(f"{provider_name}: {summary}")

        if provider_scores:
            score = max(0.0, min(10.0, sum(provider_scores) / len(provider_scores)))
        else:
            score = self._score_from_issues(all_issues)

        summary = " | ".join(provider_summaries) if provider_summaries else self._build_summary(all_issues, score)
        return AnalyzerResult(
            analyzer_name=self.name,
            score=round(score, 2),
            issues=all_issues,
            summary=summary,
        )

    def _configured_providers(self) -> dict[str, dict[str, str]]:
        provider_map = {
            "coderabbit": {
                "url": settings.AI_CODERABBIT_API_URL.strip(),
                "api_key": settings.AI_CODERABBIT_API_KEY.strip(),
            },
            "greptile": {
                "url": settings.AI_GREPTILE_API_URL.strip(),
                "api_key": settings.AI_GREPTILE_API_KEY.strip(),
            },
            "openrouter": {
                "url": settings.AI_OPENROUTER_API_URL.strip(),
                "api_key": settings.AI_OPENROUTER_API_KEY.strip(),
            },
        }

        configured: dict[str, dict[str, str]] = {}
        for provider in settings.AI_PROVIDERS:
            key = provider.strip().lower()
            conf = provider_map.get(key)
            if conf and conf["url"]:
                configured[key] = conf
        return configured

    def _call_provider(
        self,
        provider_name: str,
        url: str,
        api_key: str,
        files_payload: list[dict[str, Any]],
    ) -> tuple[list[Issue], float | None, str]:
        if provider_name == "openrouter":
            return self._call_openrouter(url, api_key, files_payload)

        payload = {
            "provider": provider_name,
            "files": files_payload,
            "limits": {
                "max_files": settings.AI_MAX_FILES,
                "max_chars_per_file": settings.AI_MAX_CHARS_PER_FILE,
            },
        }

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            return (
                [
                    Issue(
                        severity="warning",
                        message=f"{provider_name} returned HTTP {exc.code}",
                        file="*",
                        line=None,
                        rule=f"{provider_name}_http_error",
                    )
                ],
                None,
                "request failed",
            )
        except Exception as exc:
            return (
                [
                    Issue(
                        severity="warning",
                        message=f"{provider_name} integration unavailable: {exc}",
                        file="*",
                        line=None,
                        rule=f"{provider_name}_unavailable",
                    )
                ],
                None,
                "integration unavailable",
            )

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return (
                [
                    Issue(
                        severity="warning",
                        message=f"{provider_name} returned non-JSON response",
                        file="*",
                        line=None,
                        rule=f"{provider_name}_invalid_response",
                    )
                ],
                None,
                "invalid response",
            )

        issues = self._extract_issues(data, provider_name)
        score = self._extract_score(data)
        summary = self._extract_summary(data, provider_name, issues)
        return issues, score, summary

    def _call_openrouter(
        self,
        url: str,
        api_key: str,
        files_payload: list[dict[str, Any]],
    ) -> tuple[list[Issue], float | None, str]:
        if not api_key:
            return (
                [
                    Issue(
                        severity="warning",
                        message="openrouter api key is not configured",
                        file="*",
                        line=None,
                        rule="openrouter_missing_api_key",
                    )
                ],
                None,
                "missing api key",
            )

        selected_model = self._select_openrouter_model()
        prompt_payload = {
            "task": "code_quality_review",
            "instructions": (
                "Return ONLY valid JSON with shape: "
                '{"summary": str, "score": number(0-10), '
                '"issues": [{"severity": "error|warning|info", "message": str, '
                '"file": str, "line": number|null, "column": number|null, "rule": str|null}]}'
            ),
            "files": files_payload,
        }

        payload = {
            "model": selected_model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict code quality reviewer. "
                        "Output valid JSON only. No markdown."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt_payload)},
            ],
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if settings.AI_OPENROUTER_HTTP_REFERER:
            headers["HTTP-Referer"] = settings.AI_OPENROUTER_HTTP_REFERER
        if settings.AI_OPENROUTER_APP_TITLE:
            headers["X-OpenRouter-Title"] = settings.AI_OPENROUTER_APP_TITLE

        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            return (
                [
                    Issue(
                        severity="warning",
                        message=f"openrouter returned HTTP {exc.code}",
                        file="*",
                        line=None,
                        rule="openrouter_http_error",
                    )
                ],
                None,
                "request failed",
            )
        except Exception as exc:
            return (
                [
                    Issue(
                        severity="warning",
                        message=f"openrouter integration unavailable: {exc}",
                        file="*",
                        line=None,
                        rule="openrouter_unavailable",
                    )
                ],
                None,
                "integration unavailable",
            )

        try:
            response_data = json.loads(body)
        except json.JSONDecodeError:
            return (
                [
                    Issue(
                        severity="warning",
                        message="openrouter returned non-json payload",
                        file="*",
                        line=None,
                        rule="openrouter_invalid_response",
                    )
                ],
                None,
                "invalid response",
            )

        model_data = self._extract_openrouter_model_json(response_data)
        if model_data is None:
            return (
                [
                    Issue(
                        severity="warning",
                        message="openrouter response did not contain structured review JSON",
                        file="*",
                        line=None,
                        rule="openrouter_unstructured_output",
                    )
                ],
                None,
                f"model {selected_model} returned unstructured output",
            )

        issues = self._extract_issues(model_data, "openrouter")
        score = self._extract_score(model_data)
        summary = self._extract_summary(model_data, "openrouter", issues)
        return issues, score, f"model {selected_model}: {summary}"

    def _select_openrouter_model(self) -> str:
        preferred = settings.AI_OPENROUTER_MODEL.strip()
        free_models = [m.strip() for m in settings.AI_OPENROUTER_FREE_MODELS if m.strip()]
        if preferred:
            return preferred
        if free_models:
            return free_models[0]
        return "openai/gpt-oss-120b:free"

    def _extract_openrouter_model_json(self, response_data: Any) -> dict[str, Any] | None:
        if not isinstance(response_data, dict):
            return None

        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            return None

        first = choices[0]
        if not isinstance(first, dict):
            return None

        message = first.get("message")
        if not isinstance(message, dict):
            return None

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            return None

        return self._parse_json_from_text(content)

    def _parse_json_from_text(self, text: str) -> dict[str, Any] | None:
        stripped = text.strip()

        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
        if fenced_match:
            candidate = fenced_match.group(1)
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        object_match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if object_match:
            candidate = object_match.group(0)
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return None

        return None

    def _extract_issues(self, data: Any, provider_name: str) -> list[Issue]:
        if not isinstance(data, dict):
            return []

        raw_items = data.get("issues") or data.get("findings") or []
        if not isinstance(raw_items, list):
            return []

        issues: list[Issue] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            message = str(item.get("message") or item.get("title") or "AI finding")
            file_path = str(item.get("file") or item.get("file_path") or "*")
            line = self._to_int_or_none(item.get("line"))
            rule = str(item.get("rule") or item.get("id") or f"{provider_name}_finding")
            severity = self._normalize_severity(item.get("severity"))

            issues.append(
                Issue(
                    severity=severity,
                    message=message,
                    file=file_path,
                    line=line,
                    column=self._to_int_or_none(item.get("column")),
                    line_content=item.get("line_content"),
                    rule=rule,
                )
            )

        return issues

    def _extract_score(self, data: Any) -> float | None:
        if not isinstance(data, dict):
            return None

        for key in ("score", "overall_score", "quality_score"):
            value = data.get(key)
            try:
                if value is not None:
                    score = float(value)
                    return max(0.0, min(10.0, score))
            except (TypeError, ValueError):
                continue
        return None

    def _extract_summary(self, data: Any, provider_name: str, issues: list[Issue]) -> str:
        if isinstance(data, dict):
            summary = data.get("summary") or data.get("message")
            if summary:
                return str(summary)
        return f"{provider_name} findings: {len(issues)}"

    def _score_from_issues(self, issues: list[Issue]) -> float:
        score = 10.0
        for issue in issues:
            if issue.severity == "error":
                score -= 1.5
            elif issue.severity == "warning":
                score -= 0.5
            else:
                score -= 0.1
        return max(0.0, score)

    def _detect_language(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
        }
        return language_map.get(suffix, "text")

    def _normalize_severity(self, value: Any) -> str:
        if not value:
            return "warning"
        normalized = str(value).strip().lower()
        if normalized in {"critical", "high", "error", "err"}:
            return "error"
        if normalized in {"medium", "warning", "warn"}:
            return "warning"
        return "info"

    def _to_int_or_none(self, value: Any) -> int | None:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None
