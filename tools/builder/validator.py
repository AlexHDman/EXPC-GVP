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
    this-public-repository-only business rules, and (Phase 01.1) the
    EFFECTIVE per-alias ambiguity/policy/auto_replace safety invariant
    -- which requires merging an alias's own fields with its entity's
    fields, something the schema's alias_entry $def cannot see across.

What is intentionally NOT re-checked here because the schema already
enforces it byte-for-byte: required keys, enum membership, the entity-
level ambiguity/policy -> auto_replace cross-field constraint, and a
LOCALLY self-contradictory structured alias (i.e. one alias object that
by itself states both ambiguity=high and auto_replace=true). Re-deriving
those in Python would be exactly the "duplicate the schema by hand"
anti-pattern the Phase 01.0 brief warns against.
"""
import json
from pathlib import Path
from typing import List, Tuple

import jsonschema

from .normalize import normalize_for_comparison
from .policy import alias_text, is_effective_policy_safe, resolve_effective_policy

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

        # Within-entity: duplicate aliases after normalization. Works
        # across both alias representations -- alias_text() extracts the
        # comparable string from a plain-string or a structured entry
        # alike, so a legacy string and a structured object naming the
        # same text are caught as duplicates too. The schema's
        # uniqueItems only catches exact-representation duplicates, not
        # e.g. case/whitespace variants or string-vs-object duplicates.
        for lang, forms in aliases.items():
            normed_forms = [normalize_for_comparison(alias_text(f)) for f in forms]
            dupes = {f for f in normed_forms if normed_forms.count(f) > 1}
            if dupes:
                errors.append(
                    f"{path}: duplicate alias(es) in aliases['{lang}'] "
                    f"after normalization: {sorted(dupes)}"
                )

        # Per-alias effective policy safety (Phase 01.1). The schema's
        # alias_entry $def already rejects a structured alias that states
        # ambiguity=high/policy=context_required without ALSO stating
        # auto_replace=false on that same object -- but it cannot reach
        # across to the entity's own fields. The gap this closes is the
        # alias that overrides ONLY auto_replace=true while ambiguity/
        # policy are left to inherit an unsafe entity-level value. See
        # tools/builder/policy.py for the full explanation.
        for lang, forms in aliases.items():
            for form in forms:
                effective = resolve_effective_policy(form, data)
                if not is_effective_policy_safe(effective):
                    errors.append(
                        f"{path}: alias '{effective.value}' in aliases['{lang}'] has an "
                        f"unsafe effective policy (ambiguity={effective.ambiguity}, "
                        f"policy={effective.policy}, auto_replace={effective.auto_replace}); "
                        f"ambiguity=high or policy=context_required requires "
                        f"auto_replace=false, whether inherited from the entity or set "
                        f"directly on the alias"
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
