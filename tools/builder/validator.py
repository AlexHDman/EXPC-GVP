"""
Stages 2 and 3 of the Builder pipeline: JSON Schema validation, then
semantic (cross-record / runtime-contract) validation.

Deliberate division of responsibility (see docs/01_DATA_SCHEMA.md):
  - schema/gvp.schema.json is the *structural* contract: field types,
    required keys, enums, and the two cross-field constraints
    (ambiguity=high / policy=context_required => auto_replace=false)
    that JSON Schema's allOf/if/then can express directly.
  - This module's semantic checks are things JSON Schema structurally
    cannot express or that only make sense across multiple records:
    cross-record uniqueness, normalization-aware duplicate detection,
    and this-public-repository-only business rules.

What is intentionally NOT re-checked here because the schema already
enforces it byte-for-byte: required keys, enum membership, and the
ambiguity/policy -> auto_replace cross-field constraint. Re-deriving
those in Python would be exactly the "duplicate the schema by hand"
anti-pattern the Phase 01.0 brief warns against.
"""
import json
from pathlib import Path
from typing import List, Tuple

import jsonschema

from .normalize import normalize_for_comparison

# Kept in sync with tests/test_schema.py's FORBIDDEN_TERMS. Not imported
# from there because tests/ should not be a runtime dependency of tools/.
FORBIDDEN_TERMS = {"expc", "fohow", "rus177"}

PUBLIC_LAYERS = {"global", "domain"}


def load_schema(schema_path: Path) -> dict:
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def make_validator(schema: dict) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(schema)


def validate_schema_conformance(
    validator: jsonschema.Draft202012Validator,
    path: Path,
    data: dict,
) -> List[str]:
    errors = []
    for error in validator.iter_errors(data):
        location = "/".join(str(p) for p in error.path) or "<root>"
        errors.append(f"{path}: [{location}] {error.message}")
    return errors


def validate_semantics(entities_by_path: List[Tuple[Path, dict]]) -> List[str]:
    """
    Cross-record and normalization-aware checks. Assumes every entity has
    already passed validate_schema_conformance (so required keys exist)
    -- this is only meaningful as stage 3, after stage 2 has passed.
    """
    errors: List[str] = []

    seen_ids: dict = {}
    seen_canonicals: dict = {}

    for path, data in entities_by_path:
        entity_id = data.get("id")
        canonical = data.get("canonical", "")
        layer = data.get("layer")
        aliases = data.get("aliases", {})

        # Cross-record: unique IDs.
        if entity_id in seen_ids:
            errors.append(
                f"{path}: duplicate id '{entity_id}' also used by {seen_ids[entity_id]}"
            )
        else:
            seen_ids[entity_id] = path

        # Non-empty canonical *after* normalization. The schema's
        # minLength:1 only rejects the empty string, not e.g. a
        # whitespace-only value -- that gap is exactly what this check
        # closes.
        normalized_canonical = normalize_for_comparison(canonical)
        if not normalized_canonical:
            errors.append(f"{path}: canonical is empty after normalization")

        # Cross-record: duplicate canonical after normalization.
        if normalized_canonical:
            if normalized_canonical in seen_canonicals:
                errors.append(
                    f"{path}: canonical '{canonical}' normalizes to the same "
                    f"value as {seen_canonicals[normalized_canonical]}"
                )
            else:
                seen_canonicals[normalized_canonical] = path

        # Within-entity: duplicate aliases after normalization. The
        # schema's uniqueItems only catches exact string duplicates, not
        # e.g. case/whitespace variants of the same alias.
        for lang, forms in aliases.items():
            normed_forms = [normalize_for_comparison(f) for f in forms]
            dupes = {f for f in normed_forms if normed_forms.count(f) > 1}
            if dupes:
                errors.append(
                    f"{path}: duplicate alias(es) in aliases['{lang}'] "
                    f"after normalization: {sorted(dupes)}"
                )

        # Public-repository business rule: schema allows layer in
        # {global, domain, organization, personal} because the same
        # schema is reused by private stores; this repository's own
        # data/ must only ever contain global/domain.
        if layer not in PUBLIC_LAYERS:
            errors.append(
                f"{path}: layer '{layer}' is not allowed in this public repository"
            )

        # Public-repository business rule: fixture/data must never
        # contain out-of-scope organization/private vocabulary.
        haystack = json.dumps(data, ensure_ascii=False).lower()
        for term in FORBIDDEN_TERMS:
            if term in haystack:
                errors.append(f"{path}: forbidden out-of-scope term '{term}' present")

    return errors
