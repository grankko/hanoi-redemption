from pathlib import Path

from hanoi_redemption.credentials import find_openai_credentials


def test_explicit_environment_wins(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("OPENAI_API_KEY=dotenv-key\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    credentials = find_openai_credentials(project_dir=tmp_path)

    assert credentials is not None
    assert credentials.api_key == "environment-key"


def test_dotenv_is_the_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=dotenv-key\n", encoding="utf-8")

    credentials = find_openai_credentials(project_dir=tmp_path)

    assert credentials is not None
    assert credentials.api_key == "dotenv-key"
    assert credentials.source == "the project .env file"


def test_missing_credentials_returns_none(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert find_openai_credentials(project_dir=tmp_path) is None
