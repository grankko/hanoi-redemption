import json
from pathlib import Path

from hanoi_redemption.credentials import find_openai_credentials


def write_explain_config(path: Path, key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"OpenAi": {"ApiKey": key}}), encoding="utf-8")


def test_explicit_environment_wins(monkeypatch, tmp_path: Path) -> None:
    explain = tmp_path / "explain.json"
    write_explain_config(explain, "explain-key")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=dotenv-key\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    credentials = find_openai_credentials(project_dir=tmp_path, explain_config=explain)

    assert credentials is not None
    assert credentials.api_key == "environment-key"


def test_explain_config_is_reused_without_copying_key(monkeypatch, tmp_path: Path) -> None:
    explain = tmp_path / "explain.json"
    write_explain_config(explain, "explain-key")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=stale-key\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    credentials = find_openai_credentials(project_dir=tmp_path, explain_config=explain)

    assert credentials is not None
    assert credentials.api_key == "explain-key"
    assert credentials.source == str(explain)


def test_dotenv_is_the_final_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=dotenv-key\n", encoding="utf-8")

    credentials = find_openai_credentials(
        project_dir=tmp_path, explain_config=tmp_path / "missing.json"
    )

    assert credentials is not None
    assert credentials.api_key == "dotenv-key"
