"""Tests for embeddings module."""

from __future__ import annotations

from fougasse.embeddings import deserialize_vector, serialize_vector


def test_serialize_vector() -> None:
    vec = [0.1, 0.2, 0.3, 0.4]
    data = serialize_vector(vec)
    assert isinstance(data, bytes)
    assert len(data) == 4 * 4  # 4 floats * 4 bytes


def test_deserialize_vector() -> None:
    vec = [0.1, 0.2, 0.3, 0.4]
    data = serialize_vector(vec)
    restored = deserialize_vector(data, dim=4)
    for a, b in zip(vec, restored):
        assert abs(a - b) < 1e-6


def test_roundtrip() -> None:
    vec = [float(i) / 100.0 for i in range(768)]
    data = serialize_vector(vec)
    restored = deserialize_vector(data, dim=768)
    assert len(restored) == 768
    for a, b in zip(vec, restored):
        assert abs(a - b) < 1e-6
