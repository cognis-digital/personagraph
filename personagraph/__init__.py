"""PERSONAGRAPH - Identity resolution dossier.

Cross-platform OSINT correlation for usernames, emails, and phone numbers.
Given a single identifier, PERSONAGRAPH derives candidate identifiers,
builds a deterministic catalog of where they could surface across known
platforms, scores confidence, and emits a structured dossier.

Standard library only. Zero network calls in the engine itself: it produces
candidate target URLs and a confidence model that a caller (or a separate
checked-out network probe) can act on. This keeps the core fully testable
and offline.
"""
from .core import (
    Identifier,
    classify_identifier,
    derive_usernames,
    build_dossier,
    PLATFORMS,
)

TOOL_NAME = "personagraph"
TOOL_VERSION = "1.0.0"

__all__ = [
    "TOOL_NAME",
    "TOOL_VERSION",
    "Identifier",
    "classify_identifier",
    "derive_usernames",
    "build_dossier",
    "PLATFORMS",
]
