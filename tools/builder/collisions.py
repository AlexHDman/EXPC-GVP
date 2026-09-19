"""
Stage 4 (after normalization) of the Builder pipeline: collision analysis.

Implements docs/03_COLLISION_POLICY.md as executable checks, at
alias-level granularity (Phase 01.1 -- Phase 01.0 reasoned at whole-entity
granularity; see docs/03_COLLISION_POLICY.md's changelog note for why
that was a known simplification). Every alias's EFFECTIVE policy
(tools/builder/policy.py: entity defaults merged with any per-alias
override) is classified as one of:

  - safe: effective auto_replace is True and nothing else flags it.
    Not surfaced separately -- the absence of an alias from `contextual`
    and `blocking` below means it was judged safe.
  - blocking: a genuine, unsafe conflict. A normalized alias value is
    shared by two or more different entities AND at least one of them
    has effective auto_replace=true for it -- i.e. some owner's data
    asserts "safe to blindly replace" for a string that does not
    uniquely identify one canonical entity. That is a contradiction in
    the data itself and must fail the build.
  - contextual: a known, already-flagged, non-blocking ambiguity: any
    alias whose effective policy is not "freely safe to auto-replace"
    (ambiguity != low, policy == context_required, or auto_replace ==
    false), or a legitimately shared alias where every owner's effective
    auto_replace is already false.

Fail-safe principle (docs/03_COLLISION_POLICY.md): if the Builder cannot
positively establish that an alias is safe, it is not treated as safe --
"safe" is never the default; every alias must earn it via an explicit
effective policy of low ambiguity, canonical_preferred, auto_replace=true.

This module only *analyzes* the dataset -- it does not implement a
replacement/matching engine, and no fuzzy/context/NLP classification is
attempted (Phase 01.0/01.1 scope guard).
"""
from typing import List, Tuple

from .normalize import normalize_for_comparison
from .policy import resolve_effective_policy


def analyze_collisions(entities: List[dict]) -> Tuple[List[dict], List[dict]]:
    # (lang, normalized_alias_value) -> list of (entity_id, EffectivePolicy)
    alias_index: dict = {}
    for entity in entities:
        for lang, forms in entity.get("aliases", {}).items():
            for form in forms:
                effective = resolve_effective_policy(form, entity)
                key = (lang, normalize_for_comparison(effective.value))
                alias_index.setdefault(key, []).append((entity["id"], effective))

    blocking: List[dict] = []
    # (entity_id, lang, normalized_alias_value) -> True if this alias is
    # part of a cross-entity collision (blocking or not).
    shared_alias_keys: set = set()

    for (lang, normalized_alias), owners in sorted(alias_index.items()):
        owner_ids = sorted({entity_id for entity_id, _ in owners})
        if len(owner_ids) <= 1:
            continue
        for entity_id, _ in owners:
            shared_alias_keys.add((entity_id, lang, normalized_alias))
        unsafe = any(effective.auto_replace for _, effective in owners)
        if unsafe:
            blocking.append(
                {
                    "type": "alias_collision",
                    "language": lang,
                    "alias": normalized_alias,
                    "entities": owner_ids,
                    "reason": (
                        "alias is shared across entities while at least one "
                        "of them has an effective auto_replace=true for it"
                    ),
                }
            )

    contextual: List[dict] = []
    for entity in sorted(entities, key=lambda e: e["id"]):
        entity_id = entity["id"]
        for lang, forms in entity.get("aliases", {}).items():
            for form in forms:
                effective = resolve_effective_policy(form, entity)
                normalized_alias = normalize_for_comparison(effective.value)
                shared = (entity_id, lang, normalized_alias) in shared_alias_keys
                flagged = (
                    effective.ambiguity in ("medium", "high")
                    or effective.policy == "context_required"
                    or effective.auto_replace is False
                    or shared
                )
                if flagged:
                    contextual.append(
                        {
                            "type": "contextual_alias",
                            "entity": entity_id,
                            "alias": effective.value,
                            "language": lang,
                            "ambiguity": effective.ambiguity,
                            "policy": effective.policy,
                            "auto_replace": effective.auto_replace,
                            "overridden_fields": sorted(effective.overridden_fields),
                            "shared_alias": shared,
                        }
                    )

    return blocking, contextual
