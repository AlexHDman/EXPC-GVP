"""
Normalization used ONLY for comparison/duplicate/collision detection.

This module must never be used to alter what gets written into
dist/gvp.json -- canonical spelling in the output is always the
verbatim, curator-approved string from the source fixture file
(docs/01_DATA_SCHEMA.md: "prefer canonical original").

Deliberately NOT implemented here (Phase 01.0 scope guard):
transliteration, fuzzy/phonetic matching, stemming, or any other NLP.
"""
import unicodedata


def normalize_for_comparison(value: str) -> str:
    """
    Deterministic, locale-independent normalization for equality checks:
    Unicode NFC, trim, collapse internal whitespace, casefold.

    casefold() (not lower()) is used because it is the Unicode-correct
    choice for case-insensitive comparison across scripts, including
    Cyrillic, and is deterministic given fixed Unicode data.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", value)
    text = text.strip()
    text = " ".join(text.split())
    return text.casefold()
