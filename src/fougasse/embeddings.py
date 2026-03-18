"""Embedding model wrapper for Fougasse using sentence-transformers."""

from __future__ import annotations

import struct
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
_model_name: str = ""


def _get_device() -> str:
    """Auto-detect best available device."""
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_model(
    model_name: str = "BAAI/bge-base-en-v1.5", cache_dir: Path | None = None
) -> SentenceTransformer:
    """Load the embedding model (cached singleton)."""
    global _model, _model_name

    if _model is not None and _model_name == model_name:
        return _model

    device = _get_device()
    cache_path = str(cache_dir) if cache_dir else None
    _model = SentenceTransformer(model_name, device=device, cache_folder=cache_path)
    _model_name = model_name
    return _model


def encode(text: str, model: SentenceTransformer | None = None) -> list[float]:
    """Encode a single text into a normalized embedding vector."""
    m = model or load_model()
    embedding = m.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def encode_batch(texts: list[str], model: SentenceTransformer | None = None) -> list[list[float]]:
    """Encode multiple texts into normalized embedding vectors."""
    if not texts:
        return []
    m = model or load_model()
    embeddings = m.encode(texts, normalize_embeddings=True, batch_size=32)
    return [e.tolist() for e in embeddings]


def serialize_vector(vector: list[float]) -> bytes:
    """Serialize a float vector to binary format for sqlite-vec."""
    return struct.pack(f"{len(vector)}f", *vector)


def deserialize_vector(data: bytes, dim: int = 768) -> list[float]:
    """Deserialize binary data back to a float vector."""
    return list(struct.unpack(f"{dim}f", data))
