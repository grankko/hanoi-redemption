"""Stable protocol identifiers and clear user-facing names."""

from __future__ import annotations


def normalize_protocol(protocol: str) -> str:
    """Map the public ``paper`` alias to the persisted legacy identifier."""

    return "apple" if protocol == "paper" else protocol


def protocol_label(protocol: str) -> str:
    normalized = normalize_protocol(protocol)
    if normalized == "apple":
        return "paper (one-shot)"
    if normalized == "interactive":
        return "interactive play"
    return protocol
