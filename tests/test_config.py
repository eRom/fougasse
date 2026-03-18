"""Tests for configuration module."""

from __future__ import annotations

from pathlib import Path

from fougasse.config import FougasseConfig, load_config


def test_default_config() -> None:
    config = FougasseConfig()
    assert config.model_name == "BAAI/bge-base-en-v1.5"
    assert config.embedding_dim == 768
    assert config.max_results == 10
    assert config.default_vault == "default"
    assert config.rrf_k == 60
    assert config.server_transport == "stdio"


def test_env_override(monkeypatch: object) -> None:

    monkeypatch.setenv("FOUGASSE_MAX_RESULTS", "42")  # type: ignore[attr-defined]
    monkeypatch.setenv("FOUGASSE_DEFAULT_VAULT", "work")  # type: ignore[attr-defined]
    monkeypatch.setenv("FOUGASSE_RERANKER_ENABLED", "true")  # type: ignore[attr-defined]

    config = load_config(config_path=Path("/nonexistent/config.toml"))
    assert config.max_results == 42
    assert config.default_vault == "work"
    assert config.reranker_enabled is True


def test_toml_loading(tmp_path: Path) -> None:
    toml_content = """
[search]
max_results = 25
rrf_k = 100

[embeddings]
model_name = "test-model"
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)
    assert config.max_results == 25
    assert config.rrf_k == 100
    assert config.model_name == "test-model"


def test_ensure_dirs(tmp_path: Path) -> None:
    config = FougasseConfig(
        data_dir=tmp_path / "fougasse_test",
        models_dir=tmp_path / "fougasse_test" / "models",
    )
    config.ensure_dirs()
    assert config.data_dir.exists()
    assert config.models_dir.exists()
