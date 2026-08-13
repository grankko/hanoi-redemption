"""Project-local OpenAI credential discovery without logging secrets."""

from __future__ import annotations

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
) -> OpenAICredentials | None:
    """Resolve a key from the environment or the project's ignored ``.env`` file."""

    environment_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if environment_key:
        return OpenAICredentials(environment_key, "the OPENAI_API_KEY environment variable")

    dotenv_path = (project_dir or Path.cwd()) / ".env"
    if dotenv_path.is_file():
        dotenv_key = str(dotenv_values(dotenv_path).get("OPENAI_API_KEY") or "").strip()
        if dotenv_key:
            return OpenAICredentials(dotenv_key, "the project .env file")

    return None
