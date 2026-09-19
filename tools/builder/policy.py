"""
Per-alias effective policy resolution (Phase 01.1).

Per docs/01_DATA_SCHEMA.md ("Per-alias policy model") and
docs/03_COLLISION_POLICY.md, an alias entry (one item of
aliases['<lang>']) is either:

  - a plain string -- the legacy/simple form, unchanged since schema
    0.1.0. Fully inherits ambiguity/policy/auto_replace from the entity.
  - a structured object {"value": ..., "ambiguity"?, "policy"?,
    "auto_replace"?} -- each of the three fields independently overrides
    the entity's field of the same name if present; any field left out
    inherits the entity's value of that field. This is per-field
    inheritance, not "any override present means ignore the entity
    entirely" -- an alias can override just `ambiguity` and still
    inherit the entity's `policy`/`auto_replace`.

This module only *resolves* what the effective policy for a given alias
is and whether that effective policy is safe. It does not implement
alias matching/replacement against arbitrary text -- that remains a
future consumer's responsibility, not the Builder's (Phase 01.0/01.1
scope guard).
"""
from typing import NamedTuple, Union

AliasEntry = Union[str, dict]


class EffectivePolicy(NamedTuple):
    value: str
    ambiguity: str
    policy: str
    auto_replace: bool
    overridden_fields: frozenset


def alias_text(alias_entry: AliasEntry) -> str:
    """Extract the alias text, regardless of string vs. structured form."""
    if isinstance(alias_entry, str):
        return alias_entry
    return alias_entry["value"]


def resolve_effective_policy(alias_entry: AliasEntry, entity: dict) -> EffectivePolicy:
    """
    Resolve the effective (ambiguity, policy, auto_replace) for one
    alias of one entity, applying entity-default -> alias-override
    inheritance independently per field.
    """
    if isinstance(alias_entry, str):
        overrides: dict = {}
        value = alias_entry
    else:
        overrides = alias_entry
        value = alias_entry["value"]

    return EffectivePolicy(
        value=value,
        ambiguity=overrides.get("ambiguity", entity.get("ambiguity")),
        policy=overrides.get("policy", entity.get("policy")),
        auto_replace=overrides.get("auto_replace", entity.get("auto_replace")),
        overridden_fields=frozenset(
            f for f in ("ambiguity", "policy", "auto_replace") if f in overrides
        ),
    )


def is_effective_policy_safe(effective: EffectivePolicy) -> bool:
    """
    The same two safety invariants the schema enforces at entity level
    (schema/gvp.schema.json's allOf/if/then, and $defs/alias_entry's own
    local copy of them), now checked against the EFFECTIVE, merged
    per-alias policy -- which the schema itself cannot check, since it
    would require reaching across from an alias object to its sibling
    entity-level fields:

      effective.ambiguity == "high"          => effective.auto_replace must be False
      effective.policy == "context_required" => effective.auto_replace must be False

    This is the authoritative enforcement point for the "alias metadata
    must never weaken the safety invariant" rule. The schema's own
    alias_entry $def already rejects a structured alias that states
    ambiguity=high or policy=context_required WITHOUT also stating
    auto_replace=false on that same alias object -- but it cannot see
    across from the alias object to its entity's fields. So the gap this
    function closes is the opposite direction: an alias that overrides
    ONLY auto_replace=true, while ambiguity/policy are left to inherit
    an unsafe entity-level ambiguity=high or policy=context_required.
    That combination is invisible to the schema and only catchable here,
    after the two objects have been merged.
    """
    if effective.ambiguity == "high" and effective.auto_replace is not False:
        return False
    if effective.policy == "context_required" and effective.auto_replace is not False:
        return False
    return True
