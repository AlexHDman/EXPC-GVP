"""
Phase 00.2 tests for EXPC-GVP.

Scope: schema validity + fixture data (data/curated/) correctness only.
No Builder, no SQLite pack, no manifest/updater, no CI wiring is assumed
or exercised here -- see docs/00_ARCHITECTURE.md for what does not exist yet.
"""
import glob
import json
import os
import unicodedata

import jsonschema
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(REPO_ROOT, "schema", "gvp.schema.json")
CURATED_DIR = os.path.join(REPO_ROOT, "data", "curated")

# Known-keys allow-list for this repository's own fixture data. The schema
# itself uses additionalProperties: true for forward compatibility (see
# docs/01_DATA_SCHEMA.md "Forward compatibility"); this stricter check
# catches our own typos in data/curated/ without constraining the schema.
KNOWN_ENTITY_KEYS = {
    "id", "kind", "layer", "language", "canonical", "aliases",
    "ru_equivalent", "ru_transcription", "policy", "ambiguity",
    "auto_replace", "provenance",
}
KNOWN_PROVENANCE_KEYS = {
    "source", "source_url", "source_id", "license", "confidence",
    "last_verified",
}


def _load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _fixture_paths():
    return sorted(glob.glob(os.path.join(CURATED_DIR, "*.json")))


def _load_fixture(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def schema():
    return _load_schema()


@pytest.fixture(scope="module")
def validator(schema):
    return jsonschema.Draft202012Validator(schema)


@pytest.fixture(scope="module")
def fixture_paths():
    paths = _fixture_paths()
    assert paths, "expected at least one fixture file in data/curated/"
    return paths


@pytest.fixture(scope="module")
def entities(fixture_paths):
    return [(p, _load_fixture(p)) for p in fixture_paths]


# --- schema validity -------------------------------------------------------

def test_schema_is_valid_draft_2020_12(schema):
    jsonschema.Draft202012Validator.check_schema(schema)


def test_fixture_count_in_expected_range(fixture_paths):
    # Phase 00.2 asks for a small fixture set, roughly 10-20 entities.
    assert 10 <= len(fixture_paths) <= 20


# --- per-entity schema validation ------------------------------------------

@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_fixture_validates_against_schema(path, validator):
    data = _load_fixture(path)
    errors = list(validator.iter_errors(data))
    assert not errors, f"{path} failed schema validation: {errors}"


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_fixture_has_only_known_keys(path):
    data = _load_fixture(path)
    unknown = set(data.keys()) - KNOWN_ENTITY_KEYS
    assert not unknown, f"{path} has unexpected top-level keys: {unknown}"

    unknown_prov = set(data["provenance"].keys()) - KNOWN_PROVENANCE_KEYS
    assert not unknown_prov, f"{path} has unexpected provenance keys: {unknown_prov}"


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_canonical_non_empty(path):
    data = _load_fixture(path)
    assert isinstance(data["canonical"], str)
    assert data["canonical"].strip() != ""


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_id_matches_kind_slug_convention(path):
    data = _load_fixture(path)
    prefix, _, slug = data["id"].partition(".")
    assert prefix == data["kind"], (
        f"{path}: id prefix '{prefix}' does not match kind '{data['kind']}'"
    )
    assert slug, f"{path}: id has no slug after the kind prefix"


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_fixture_only_uses_public_layers(path):
    # This public repository's data/ may only ever contain global/domain
    # entries -- organization/personal are valid schema values but must
    # never appear as real entities here (docs/02_VOCABULARY_LAYERS.md).
    data = _load_fixture(path)
    assert data["layer"] in ("global", "domain"), (
        f"{path}: layer '{data['layer']}' is not allowed in the public repository"
    )


# --- unique IDs --------------------------------------------------------

def test_unique_ids_across_fixtures(entities):
    ids = [data["id"] for _, data in entities]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"duplicate id(s) across data/curated/: {duplicates}"


# --- alias normalization / duplication ----------------------------------

@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_alias_keys_are_valid_language_codes(path):
    data = _load_fixture(path)
    for lang_code, forms in data["aliases"].items():
        assert lang_code.islower() and len(lang_code) == 2, (
            f"{path}: alias language key '{lang_code}' is not a 2-letter lowercase code"
        )
        assert isinstance(forms, list) and forms, (
            f"{path}: aliases['{lang_code}'] must be a non-empty list"
        )


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_no_duplicate_aliases_inside_entity(path):
    data = _load_fixture(path)
    for lang_code, forms in data["aliases"].items():
        lowered = [f.lower() for f in forms]
        duplicates = {f for f in lowered if lowered.count(f) > 1}
        assert not duplicates, (
            f"{path}: duplicate alias(es) within aliases['{lang_code}']: {duplicates}"
        )


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_aliases_are_unicode_nfc_normalized(path):
    data = _load_fixture(path)
    for lang_code, forms in data["aliases"].items():
        for form in forms:
            assert form == unicodedata.normalize("NFC", form), (
                f"{path}: alias '{form}' in aliases['{lang_code}'] is not NFC-normalized"
            )


def test_fixture_includes_russian_unicode_aliases(entities):
    # Sanity check that the fixture actually exercises non-Latin (Cyrillic)
    # alias data, not just ASCII.
    has_cyrillic = any(
        any(
            any(0x0400 <= ord(ch) <= 0x04FF for ch in form)
            for forms in data["aliases"].values()
            for form in forms
        )
        for _, data in entities
    )
    assert has_cyrillic, "expected at least one Cyrillic alias across the fixture set"


# --- collisions between entities -----------------------------------------

def test_no_alias_collisions_between_entities(entities):
    """
    An alias string that maps to two or more different entity ids is a
    collision (docs/03_COLLISION_POLICY.md, "Overlapping aliases"). The
    curated fixture set is expected to be collision-free; this test is a
    guard against accidentally introducing one, not a claim that collisions
    can never legitimately occur in a larger, real-world dataset.
    """
    alias_owners = {}  # (lang, normalized alias) -> set of ids
    for path, data in entities:
        for lang_code, forms in data["aliases"].items():
            for form in forms:
                key = (lang_code, form.lower())
                alias_owners.setdefault(key, set()).add(data["id"])

    collisions = {k: v for k, v in alias_owners.items() if len(v) > 1}
    assert not collisions, f"alias(es) shared by multiple entities: {collisions}"


def test_no_canonical_collisions_between_entities(entities):
    canonicals = [(data["canonical"].lower(), data["id"]) for _, data in entities]
    seen = {}
    collisions = []
    for canonical, entity_id in canonicals:
        if canonical in seen and seen[canonical] != entity_id:
            collisions.append((canonical, seen[canonical], entity_id))
        seen[canonical] = entity_id
    assert not collisions, f"canonical name collision(s): {collisions}"


# --- ambiguity / auto_replace cross-field policy --------------------------

@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_high_ambiguity_forces_auto_replace_false(path):
    data = _load_fixture(path)
    if data["ambiguity"] == "high":
        assert data["auto_replace"] is False, (
            f"{path}: ambiguity=high must imply auto_replace=false"
        )


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_context_required_forces_auto_replace_false(path):
    data = _load_fixture(path)
    if data["policy"] == "context_required":
        assert data["auto_replace"] is False, (
            f"{path}: policy=context_required must imply auto_replace=false"
        )


def test_cuda_is_the_high_ambiguity_context_required_example(entities):
    # CUDA / "куда" is the canonical worked example from
    # docs/03_COLLISION_POLICY.md -- pin it down explicitly so a future
    # edit to the fixture can't silently weaken the example.
    by_id = {data["id"]: data for _, data in entities}
    cuda = by_id.get("software.cuda")
    assert cuda is not None, "expected software.cuda fixture entity to exist"
    assert cuda["ambiguity"] == "high"
    assert cuda["policy"] == "context_required"
    assert cuda["auto_replace"] is False


# --- schema-level cross-field constraints (belt-and-suspenders) -----------

@pytest.mark.parametrize(
    "ambiguity,policy,auto_replace,should_be_valid",
    [
        ("high", "canonical_preferred", False, True),
        ("high", "canonical_preferred", True, False),
        ("low", "context_required", False, True),
        ("low", "context_required", True, False),
        ("low", "canonical_preferred", True, True),
    ],
)
def test_schema_enforces_auto_replace_constraints(
    validator, ambiguity, policy, auto_replace, should_be_valid
):
    candidate = {
        "id": "software.test_entity",
        "kind": "software",
        "layer": "global",
        "language": "en",
        "canonical": "TestEntity",
        "aliases": {},
        "ru_equivalent": None,
        "ru_transcription": None,
        "policy": policy,
        "ambiguity": ambiguity,
        "auto_replace": auto_replace,
        "provenance": {
            "source": "unverified",
            "source_url": None,
            "source_id": None,
            "license": None,
            "confidence": 0.0,
            "last_verified": None,
        },
    }
    errors = list(validator.iter_errors(candidate))
    is_valid = not errors
    assert is_valid == should_be_valid, (
        f"ambiguity={ambiguity} policy={policy} auto_replace={auto_replace}: "
        f"expected valid={should_be_valid}, got errors={errors}"
    )


# --- scope guard: fixture data must never include out-of-scope terms ------

FORBIDDEN_TERMS = {"expc", "fohow", "rus177"}


@pytest.mark.parametrize("path", _fixture_paths(), ids=os.path.basename)
def test_fixture_excludes_out_of_scope_organization_terms(path):
    data = _load_fixture(path)
    haystack = json.dumps(data, ensure_ascii=False).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in haystack, (
            f"{path}: out-of-scope organization term '{term}' must not appear in public fixture data"
        )
