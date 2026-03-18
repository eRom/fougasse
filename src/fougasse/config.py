"""Configuration management for Fougasse."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


_ENV_PREFIX = "FOUGASSE_"
_DEFAULT_DIR = Path.home() / ".fougasse"


@dataclass
class FougasseConfig:
    """Main configuration for Fougasse."""

    # Paths
    data_dir: Path = field(default_factory=lambda: _DEFAULT_DIR)
    db_path: Path = field(default_factory=lambda: _DEFAULT_DIR / "memory.db")
    learning_db_path: Path = field(default_factory=lambda: _DEFAULT_DIR / "learning.db")
    models_dir: Path = field(default_factory=lambda: _DEFAULT_DIR / "models")

    # Embeddings
    model_name: str = "BAAI/bge-base-en-v1.5"
    embedding_dim: int = 768

    # Search
    max_results: int = 10
    rrf_k: int = 60
    similarity_threshold: float = 0.35

    # Vaults
    default_vault: str = "default"

    # Vitality
    vitality_decay_d: float = 0.5
    vitality_archive_threshold: float = 0.1
    vitality_schedule_hours: int = 6

    # Contradiction detection
    contradiction_similarity_threshold: float = 0.85

    # Reranker
    reranker_enabled: bool = False
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_top_k: int = 20

    # Server
    server_name: str = "Fougasse"
    server_transport: str = "stdio"
    server_host: str = "127.0.0.1"
    server_port: int = 8765

    # Limits
    max_content_size: int = 102400  # 100KB
    max_tags_per_memory: int = 20
    max_tag_length: int = 64

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)


def _apply_env_overrides(config: FougasseConfig) -> None:
    """Override config values from environment variables."""
    for field_name in config.__dataclass_fields__:
        env_key = f"{_ENV_PREFIX}{field_name.upper()}"
        env_val = os.environ.get(env_key)
        if env_val is None:
            continue

        current = getattr(config, field_name)
        if isinstance(current, Path):
            setattr(config, field_name, Path(env_val))
        elif isinstance(current, bool):
            setattr(config, field_name, env_val.lower() in ("true", "1", "yes"))
        elif isinstance(current, int):
            setattr(config, field_name, int(env_val))
        elif isinstance(current, float):
            setattr(config, field_name, float(env_val))
        else:
            setattr(config, field_name, env_val)


def _apply_toml(config: FougasseConfig, data: dict[str, Any]) -> None:
    """Apply TOML values to config, supporting nested sections."""
    flat: dict[str, Any] = {}
    for key, val in data.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                flat[sub_key] = sub_val
        else:
            flat[key] = val

    for field_name in config.__dataclass_fields__:
        if field_name in flat:
            current = getattr(config, field_name)
            val = flat[field_name]
            if isinstance(current, Path):
                setattr(config, field_name, Path(val))
            else:
                setattr(config, field_name, type(current)(val))


def load_config(config_path: Path | None = None) -> FougasseConfig:
    """Load configuration from TOML file + env overrides."""
    config = FougasseConfig()

    # Load TOML if exists
    path = config_path or (config.data_dir / "config.toml")
    if path.exists():
        with open(path, "rb") as f:
            data = tomllib.load(f)
        _apply_toml(config, data)

    # Env overrides take precedence
    _apply_env_overrides(config)

    # Ensure paths are relative to data_dir if not absolute
    if not config.db_path.is_absolute():
        config.db_path = config.data_dir / config.db_path
    if not config.learning_db_path.is_absolute():
        config.learning_db_path = config.data_dir / config.learning_db_path

    return config
