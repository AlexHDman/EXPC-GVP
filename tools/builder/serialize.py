"""
Deterministic JSON serialization shared by every JSON artifact this
Builder writes (dist/gvp.json, manifest.json). One place, one format, so
gvp.json produced standalone (`build`) and gvp.json produced inside a
Data Pack (`package`) are byte-identical for the same input.
"""
import json


def serialize_json_deterministic(data: dict) -> bytes:
    """
    UTF-8, ensure_ascii=False (literal Cyrillic, not \\uXXXX escapes),
    2-space indent, trailing newline, `\\n` line endings -- encoded
    directly to bytes so no text-mode newline translation (e.g. Windows
    \\n -> \\r\\n) can ever apply.
    """
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
