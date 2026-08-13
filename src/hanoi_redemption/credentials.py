"""Local OpenAI credential discovery without copying or logging secrets."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True, slots=True)
class OpenAICredentials:
    api_key: str
    source: str


def find_openai_credentials(
    *,
    project_dir: Path | None = None,
    explain_config: Path | None = None,
) -> OpenAICredentials | None:
    """Resolve a key from explicit environment, Explain, or the local project.

    Explain is checked before ``.env`` because it is the user's installed,
    shared OpenAI configuration. An explicitly exported environment variable
    always wins.
    """

    environment_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if environment_key:
        return OpenAICredentials(environment_key, "the OPENAI_API_KEY environment variable")

    config_path = explain_config or Path.home() / ".config" / "explain" / "appsettings.json"
    explain_key = _read_explain_key(config_path)
    if explain_key:
        return OpenAICredentials(explain_key, str(config_path))

    dotenv_path = (project_dir or Path.cwd()) / ".env"
    if dotenv_path.is_file():
        dotenv_key = str(dotenv_values(dotenv_path).get("OPENAI_API_KEY") or "").strip()
        if dotenv_key:
            return OpenAICredentials(dotenv_key, str(dotenv_path))

    return None


def _read_explain_key(path: Path) -> str | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        value = document.get("OpenAi", {}).get("ApiKey")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()
