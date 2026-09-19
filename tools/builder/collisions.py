"""
Stage 4 (after normalization) of the Builder pipeline: collision analysis.

Implements docs/03_COLLISION_POLICY.md as executable checks. Distinguishes
two outcomes, per the Phase 01.0 brief:

  - blocking: a genuine, unsafe conflict. An alias (normalized) is shared
    by two or more different entities AND at least one of them claims
    auto_replace=true for it -- i.e. the data asserts "safe to blindly
    replace" for a string that does not uniquely identify one canonical
    entity. That is a contradiction in the data itself and must fail the
    build.
  - contextual: a known, already-flagged ambiguity that does NOT block
    the build. This covers both entities whose own ambiguity/policy/
    auto_replace fields already mark them as not safe to auto-replace
    (e.g. software.cuda / "куда" -- ambiguity=high, policy=context_required,
    auto_replace=false), and legitimately shared aliases where every
    owning entity already agrees not to auto-replace.

This module does not implement a replacement/matching engine -- it only
analyzes the dataset, per the Phase 01.0 scope guard.
"""
from typing import List, Tuple

from .normalize import normalize_for_comparison


def analyze_collisions(entities: List[dict]) -> Tuple[List[dict], List[dict]]:
    alias_index: dict = {}  # (lang, normalized_alias) -> list of (id, auto_replace)
    for entity in entities:
        for lang, forms in entity.get("aliases", {}).items():
            for form in forms:
                key = (lang, normalize_for_comparison(form))
                alias_index.setdefault(key, []).append(
                    (entity["id"], bool(entity.get("auto_replace")))
                )

    blocking: List[dict] = []
    shared_alias_owner_ids: set = set()

    for (lang, normalized_alias), owners in sorted(alias_index.items()):
        owner_ids = sorted({entity_id for entity_id, _ in owners})
        if len(owner_ids) <= 1:
            continue
        shared_alias_owner_ids.update(owner_ids)
        unsafe = any(auto_replace for _, auto_replace in owners)
        if unsafe:
            blocking.append(
                {
                    "type": "alias_collision",
                    "language": lang,
                    "alias": normalized_alias,
                    "entities": owner_ids,
                    "reason": (
                        "alias is shared across entities while at least one "
                        "of them has auto_replace=true"
                    ),
                }
            )

    contextual: List[dict] = []
    for entity in sorted(entities, key=lambda e: e["id"]):
        entity_id = entity["id"]
        shared = entity_id in shared_alias_owner_ids
        flagged = (
            entity.get("ambiguity") in ("medium", "high")
            or entity.get("policy") == "context_required"
            or entity.get("auto_replace") is False
            or shared
        )
        if flagged:
            contextual.append(
                {
                    "type": "contextual_ambiguity",
                    "entity": entity_id,
                    "ambiguity": entity.get("ambiguity"),
                    "policy": entity.get("policy"),
                    "auto_replace": entity.get("auto_replace"),
                    "shared_alias": shared,
                }
            )

    return blocking, contextual
