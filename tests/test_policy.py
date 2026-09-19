"""
Phase 01.1 tests for tools/builder/policy.py: per-alias effective policy
resolution (entity defaults -> alias overrides -> effective policy).

Uses only synthetic in-memory entity dicts (no filesystem/schema
involved) -- schema-level acceptance/rejection of the new alias_entry
shape is covered separately in tests/test_schema.py and
tests/test_builder.py.
"""
from tools.builder.policy import (
    alias_text,
    is_effective_policy_safe,
    resolve_effective_policy,
)


def make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True):
    return {
        "id": "software.alpha",
        "ambiguity": ambiguity,
        "policy": policy,
        "auto_replace": auto_replace,
    }


# --- alias_text --------------------------------------------------------

def test_alias_text_extracts_from_legacy_string():
    assert alias_text("вайфай") == "вайфай"


def test_alias_text_extracts_from_structured_object():
    assert alias_text({"value": "вафля", "ambiguity": "medium"}) == "вафля"


# --- inheritance: legacy string alias inherits entity policy wholesale ----

def test_legacy_string_alias_inherits_entity_policy():
    entity = make_entity(ambiguity="high", policy="context_required", auto_replace=False)
    effective = resolve_effective_policy("куда", entity)
    assert effective.value == "куда"
    assert effective.ambiguity == "high"
    assert effective.policy == "context_required"
    assert effective.auto_replace is False
    assert effective.overridden_fields == frozenset()


# --- structured alias without metadata also inherits entity policy -------

def test_structured_alias_without_overrides_inherits_entity_policy():
    entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    effective = resolve_effective_policy({"value": "вайфай"}, entity)
    assert effective.ambiguity == "low"
    assert effective.policy == "canonical_preferred"
    assert effective.auto_replace is True
    assert effective.overridden_fields == frozenset()


# --- structured alias with full metadata overrides entity default --------

def test_structured_alias_full_override_wins_over_entity_default():
    entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    alias = {
        "value": "вафля",
        "ambiguity": "medium",
        "policy": "canonical_preferred",
        "auto_replace": False,
    }
    effective = resolve_effective_policy(alias, entity)
    assert effective.ambiguity == "medium"
    assert effective.auto_replace is False
    assert effective.overridden_fields == {"ambiguity", "policy", "auto_replace"}


# --- per-field inheritance: partial override only replaces that field ----

def test_structured_alias_partial_override_inherits_remaining_fields():
    entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    alias = {"value": "risky", "ambiguity": "high"}  # auto_replace/policy NOT overridden
    effective = resolve_effective_policy(alias, entity)
    assert effective.ambiguity == "high"          # overridden
    assert effective.policy == "canonical_preferred"  # inherited
    assert effective.auto_replace is True           # inherited (dangerously!)
    assert effective.overridden_fields == {"ambiguity"}
    # Unsafe at the policy.py level. In practice schema/gvp.schema.json's
    # alias_entry $def would already reject this exact object shape
    # (ambiguity=high without a co-located auto_replace=false) before it
    # ever reached this function -- see
    # test_partial_override_of_only_auto_replace_is_the_real_schema_gap
    # below for the combination the schema genuinely cannot catch.
    assert is_effective_policy_safe(effective) is False


def test_partial_override_of_only_auto_replace_is_the_real_schema_gap():
    # schema/gvp.schema.json's alias_entry allOf only fires when THIS
    # alias object itself states ambiguity/policy; it cannot see the
    # entity's fields. So the combination it truly cannot catch is an
    # alias overriding ONLY auto_replace=true while ambiguity/policy
    # inherit an unsafe entity-level value -- this is what
    # tools/builder/validator.py's effective-policy check exists for.
    entity = make_entity(ambiguity="high", policy="context_required", auto_replace=False)
    alias = {"value": "unsafe", "auto_replace": True}  # only auto_replace overridden
    effective = resolve_effective_policy(alias, entity)
    assert effective.ambiguity == "high"       # inherited, unsafe
    assert effective.auto_replace is True        # overridden, unsafe combination
    assert effective.overridden_fields == {"auto_replace"}
    assert is_effective_policy_safe(effective) is False


# --- safety invariant on the EFFECTIVE (merged) result --------------------

def test_effective_high_ambiguity_with_inherited_auto_replace_true_is_unsafe():
    entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    effective = resolve_effective_policy({"value": "x", "ambiguity": "high"}, entity)
    assert is_effective_policy_safe(effective) is False


def test_effective_context_required_with_inherited_auto_replace_true_is_unsafe():
    entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    effective = resolve_effective_policy({"value": "x", "policy": "context_required"}, entity)
    assert is_effective_policy_safe(effective) is False


def test_effective_high_ambiguity_with_explicit_auto_replace_false_is_safe():
    entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    effective = resolve_effective_policy(
        {"value": "x", "ambiguity": "high", "auto_replace": False}, entity
    )
    assert is_effective_policy_safe(effective) is True


def test_effective_low_ambiguity_auto_replace_true_is_safe():
    entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    effective = resolve_effective_policy("safe-alias", entity)
    assert is_effective_policy_safe(effective) is True


# --- worked examples from docs/03_COLLISION_POLICY.md ---------------------

def test_wifi_safe_alias_effective_policy():
    wifi_entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    effective = resolve_effective_policy("вайфай", wifi_entity)
    assert (effective.ambiguity, effective.policy, effective.auto_replace) == (
        "low", "canonical_preferred", True,
    )


def test_wifi_risky_alias_effective_policy():
    wifi_entity = make_entity(ambiguity="low", policy="canonical_preferred", auto_replace=True)
    risky_alias = {
        "value": "вафля",
        "ambiguity": "medium",
        "policy": "canonical_preferred",
        "auto_replace": False,
    }
    effective = resolve_effective_policy(risky_alias, wifi_entity)
    assert (effective.ambiguity, effective.policy, effective.auto_replace) == (
        "medium", "canonical_preferred", False,
    )
    assert is_effective_policy_safe(effective) is True  # not blocking -- contextual


def test_cuda_alias_effective_policy_via_pure_inheritance():
    cuda_entity = make_entity(ambiguity="high", policy="context_required", auto_replace=False)
    effective = resolve_effective_policy("куда", cuda_entity)  # legacy string, no override
    assert (effective.ambiguity, effective.policy, effective.auto_replace) == (
        "high", "context_required", False,
    )
    assert is_effective_policy_safe(effective) is True
