"""
Phase 01.0 tests for the EXPC-GVP Builder (tools/builder/), extended in
Phase 01.1 with per-alias structured policy tests (see the "Phase 01.1"
section below; unit-level tests for tools/builder/policy.py itself live
in tests/test_policy.py).

These tests exercise the builder against synthetic, temp-directory
fixtures for failure-path scenarios (so a "bad data" test can never
touch data/curated/), and against the real repository data/curated/ +
schema/gvp.schema.json for success-path/behavioral assertions -- always
writing to a temp output path, never to dist/gvp.json, so running the
test suite never mutates the real build artifact.
"""
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

from tools.builder.build import build
from tools.builder.normalize import normalize_for_comparison

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_DATA_DIR = REPO_ROOT / "data" / "curated"
REAL_SCHEMA_PATH = REPO_ROOT / "schema" / "gvp.schema.json"


def make_entity(**overrides) -> dict:
    base = {
        "id": "software.alpha",
        "kind": "software",
        "layer": "global",
        "language": "en",
        "canonical": "Alpha",
        "aliases": {"ru": ["альфа"]},
        "ru_equivalent": None,
        "ru_transcription": "Альфа",
        "policy": "canonical_preferred",
        "ambiguity": "low",
        "auto_replace": True,
        "provenance": {
            "source": "unverified",
            "source_url": None,
            "source_id": None,
            "license": None,
            "confidence": 0.0,
            "last_verified": None,
        },
    }
    base.update(overrides)
    return base


def write_entities(data_dir: Path, entities: list) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    for entity in entities:
        path = data_dir / f"{entity['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entity, f, ensure_ascii=False, indent=2)
    return data_dir


# --- success path against the real fixture dataset -------------------------

def test_successful_build_against_real_fixture_data(tmp_path):
    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    assert not result.schema_errors
    assert not result.semantic_errors
    assert not result.blocking_collisions
    assert output_path.exists()


def test_deterministic_output_byte_identical(tmp_path):
    out_a = tmp_path / "a" / "gvp.json"
    out_b = tmp_path / "b" / "gvp.json"
    result_a = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, out_a)
    result_b = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, out_b)
    assert result_a.success and result_b.success
    assert out_a.read_bytes() == out_b.read_bytes()


def test_canonical_spelling_preserved_in_output(tmp_path):
    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in artifact["entities"]}
    assert by_id["brand.nvidia"]["canonical"] == "NVIDIA"
    assert by_id["software.cuda"]["canonical"] == "CUDA"


def test_stable_entity_ordering_by_id(tmp_path):
    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    ids = [e["id"] for e in artifact["entities"]]
    assert ids == sorted(ids)


def test_cuda_remains_contextual_not_blocking(tmp_path):
    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success
    assert result.blocking_collisions == []
    contextual_ids = {c["entity"] for c in result.contextual_collisions}
    assert "software.cuda" in contextual_ids


# --- normalization is comparison-only ---------------------------------

def test_normalize_for_comparison_does_not_mutate_output(tmp_path):
    entities = [
        make_entity(id="software.alpha", canonical="  Alpha  ", aliases={}),
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    # Output preserves the verbatim string, including surrounding
    # whitespace -- normalization is for comparison only.
    assert artifact["entities"][0]["canonical"] == "  Alpha  "


def test_unicode_nfc_vs_nfd_detected_as_duplicate_canonical(tmp_path):
    nfc_form = unicodedata.normalize("NFC", "Ёж")
    nfd_form = unicodedata.normalize("NFD", "Ёж")
    assert nfc_form != nfd_form  # sanity: genuinely different byte sequences
    assert normalize_for_comparison(nfc_form) == normalize_for_comparison(nfd_form)

    entities = [
        make_entity(id="software.alpha", canonical=nfc_form, aliases={}),
        make_entity(id="software.beta", canonical=nfd_form, aliases={}),
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert any("normalizes to the same" in e for e in result.semantic_errors)
    assert not output_path.exists()


# --- schema validation failure ---------------------------------------------

def test_invalid_schema_entity_fails(tmp_path):
    bad_entity = make_entity(ambiguity="not-a-real-level")
    write_entities(tmp_path / "data", [bad_entity])
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert result.schema_errors
    assert not output_path.exists()


# --- semantic validation failures ------------------------------------------

def test_duplicate_id_fails(tmp_path):
    e1 = make_entity(id="software.alpha", canonical="Alpha", aliases={})
    e2 = make_entity(id="software.alpha", canonical="AlphaTwo", aliases={})
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "a1.json").write_text(json.dumps(e1), encoding="utf-8")
    (data_dir / "a2.json").write_text(json.dumps(e2), encoding="utf-8")
    output_path = tmp_path / "gvp.json"
    result = build(data_dir, REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert any("duplicate id" in e for e in result.semantic_errors)
    assert not output_path.exists()


def test_duplicate_canonical_after_normalization_fails(tmp_path):
    entities = [
        make_entity(id="software.alpha", canonical="CUDA-Test", aliases={}),
        make_entity(id="software.beta", canonical="  cuda-test  ", aliases={}),
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert any("normalizes to the same" in e for e in result.semantic_errors)
    assert not output_path.exists()


def test_empty_data_dir_fails(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    output_path = tmp_path / "gvp.json"
    result = build(data_dir, REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert not output_path.exists()


# --- collision analysis: blocking vs contextual -----------------------

def test_shared_alias_both_non_auto_replace_is_contextual_not_blocking(tmp_path):
    entities = [
        make_entity(
            id="software.alpha", canonical="Alpha",
            aliases={"ru": ["shared"]}, ambiguity="medium", auto_replace=False,
        ),
        make_entity(
            id="software.beta", canonical="Beta",
            aliases={"ru": ["shared"]}, ambiguity="medium", auto_replace=False,
        ),
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    assert result.blocking_collisions == []
    contextual_ids = {c["entity"] for c in result.contextual_collisions}
    assert {"software.alpha", "software.beta"} <= contextual_ids


def test_shared_alias_with_auto_replace_true_is_blocking(tmp_path):
    entities = [
        make_entity(
            id="software.alpha", canonical="Alpha",
            aliases={"ru": ["shared"]}, ambiguity="low", auto_replace=True,
        ),
        make_entity(
            id="software.beta", canonical="Beta",
            aliases={"ru": ["shared"]}, ambiguity="low", auto_replace=True,
        ),
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert len(result.blocking_collisions) == 1
    assert set(result.blocking_collisions[0]["entities"]) == {
        "software.alpha", "software.beta",
    }
    assert not output_path.exists()


# --- safe / atomic write ------------------------------------------------

def test_failed_build_does_not_overwrite_previous_valid_artifact(tmp_path):
    output_path = tmp_path / "gvp.json"

    good_entities = [make_entity(id="software.alpha", canonical="Alpha", aliases={})]
    write_entities(tmp_path / "good", good_entities)
    good_result = build(tmp_path / "good", REAL_SCHEMA_PATH, output_path)
    assert good_result.success
    original_bytes = output_path.read_bytes()

    bad_entities = [make_entity(ambiguity="not-a-real-level")]
    write_entities(tmp_path / "bad", bad_entities)
    bad_result = build(tmp_path / "bad", REAL_SCHEMA_PATH, output_path)
    assert bad_result.success is False

    assert output_path.read_bytes() == original_bytes

    # No leftover temp files in the output directory.
    leftovers = [p for p in output_path.parent.iterdir() if p.name.startswith(".gvp-build-")]
    assert leftovers == []


def test_no_temp_files_left_after_successful_build(tmp_path):
    output_path = tmp_path / "gvp.json"
    entities = [make_entity(id="software.alpha", canonical="Alpha", aliases={})]
    write_entities(tmp_path / "data", entities)
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success
    leftovers = [p for p in output_path.parent.iterdir() if p.name.startswith(".gvp-build-")]
    assert leftovers == []


# --- CLI ---------------------------------------------------------------

def _run_cli(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "tools.builder", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_cli_success_exit_code(tmp_path):
    output_path = tmp_path / "gvp.json"
    proc = _run_cli(
        [
            "build",
            "--data-dir", str(REAL_DATA_DIR),
            "--schema", str(REAL_SCHEMA_PATH),
            "--output", str(output_path),
        ],
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "BUILD: PASS" in proc.stdout
    assert output_path.exists()


def test_cli_failure_exit_code(tmp_path):
    bad_entities = [make_entity(ambiguity="not-a-real-level")]
    write_entities(tmp_path / "data", bad_entities)
    output_path = tmp_path / "gvp.json"
    proc = _run_cli(
        [
            "build",
            "--data-dir", str(tmp_path / "data"),
            "--schema", str(REAL_SCHEMA_PATH),
            "--output", str(output_path),
        ],
        cwd=REPO_ROOT,
    )
    assert proc.returncode != 0
    assert "BUILD: FAIL" in proc.stdout
    assert not output_path.exists()


# --- Phase 01.1: per-alias structured policy -------------------------------

def test_legacy_string_alias_still_valid(tmp_path):
    entities = [make_entity(aliases={"ru": ["альфа", "алфа"]})]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    assert not result.schema_errors
    assert not result.semantic_errors


def test_structured_alias_valid(tmp_path):
    entities = [
        make_entity(
            aliases={
                "ru": [{"value": "альфа", "ambiguity": "low", "auto_replace": True}]
            }
        )
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    assert not result.schema_errors
    assert not result.semantic_errors


def test_structured_alias_overrides_entity_default_is_flagged_contextual(tmp_path):
    entities = [
        make_entity(
            ambiguity="low", policy="canonical_preferred", auto_replace=True,
            aliases={
                "ru": [
                    "safe-legacy",
                    {"value": "risky-override", "ambiguity": "high", "auto_replace": False},
                ]
            },
        )
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    contextual_aliases = {c["alias"] for c in result.contextual_collisions}
    assert "risky-override" in contextual_aliases
    assert "safe-legacy" not in contextual_aliases


def test_structured_alias_without_metadata_inherits_entity_policy(tmp_path):
    entities = [
        make_entity(
            ambiguity="high", policy="context_required", auto_replace=False,
            aliases={"ru": [{"value": "куда-подобный"}]},  # no overrides at all
        )
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    contextual = {c["alias"]: c for c in result.contextual_collisions}
    assert contextual["куда-подобный"]["ambiguity"] == "high"
    assert contextual["куда-подобный"]["policy"] == "context_required"
    assert contextual["куда-подобный"]["auto_replace"] is False


def test_effective_high_ambiguity_cannot_auto_replace(tmp_path):
    # The schema's own alias_entry allOf already rejects a structured
    # alias that states ambiguity=high without ALSO stating
    # auto_replace=false on that same alias object (see schema/
    # gvp.schema.json's $defs.alias_entry) -- so the only way to reach an
    # unsafe *effective* ambiguity=high is via the entity's own
    # (schema-valid) ambiguity=high, with an alias overriding ONLY
    # auto_replace=true (leaving ambiguity to inherit). The schema cannot
    # see across from the alias object to the entity's fields, so this
    # combination only the Builder's semantic layer (validate_semantics)
    # can catch.
    entities = [
        make_entity(
            ambiguity="high", policy="context_required", auto_replace=False,
            aliases={"ru": [{"value": "unsafe", "auto_replace": True}]},
        )
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert any("unsafe effective policy" in e for e in result.semantic_errors)
    assert not output_path.exists()


def test_effective_context_required_cannot_auto_replace(tmp_path):
    # Same gap as above, via policy=context_required instead of
    # ambiguity=high: alias overrides ONLY auto_replace=true, inheriting
    # policy=context_required from the entity.
    entities = [
        make_entity(
            ambiguity="low", policy="context_required", auto_replace=False,
            aliases={"ru": [{"value": "unsafe", "auto_replace": True}]},
        )
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert any("unsafe effective policy" in e for e in result.semantic_errors)
    assert not output_path.exists()


def test_schema_rejects_locally_contradictory_alias_before_reaching_builder(tmp_path):
    # Documents the OTHER half of the safety net: a structured alias that
    # states ambiguity=high (or policy=context_required) but does NOT
    # also state auto_replace=false on that same object is rejected by
    # the schema itself, before the Builder's semantic layer ever runs.
    entities = [
        make_entity(
            aliases={"ru": [{"value": "unsafe", "ambiguity": "high"}]},  # no auto_replace
        )
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert result.schema_errors  # rejected at the schema stage, not semantic
    assert not result.semantic_errors  # never even reached
    assert not output_path.exists()


def test_duplicate_detection_works_across_string_and_object_aliases(tmp_path):
    entities = [
        make_entity(
            aliases={"ru": ["альфа", {"value": "Альфа", "ambiguity": "low"}]},
        )
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert any("duplicate alias" in e for e in result.semantic_errors)
    assert not output_path.exists()


def test_collision_detection_uses_effective_alias_policy_not_entity_default(tmp_path):
    # Both entities default to auto_replace=True, but BOTH override this
    # specific shared alias to auto_replace=False -- the effective policy
    # is safe, so this must be contextual, not blocking, even though the
    # entity-level defaults alone would suggest otherwise.
    entities = [
        make_entity(
            id="software.alpha", canonical="Alpha", auto_replace=True,
            aliases={"ru": [{"value": "shared", "ambiguity": "medium", "auto_replace": False}]},
        ),
        make_entity(
            id="software.beta", canonical="Beta", auto_replace=True,
            aliases={"ru": [{"value": "shared", "ambiguity": "medium", "auto_replace": False}]},
        ),
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    assert result.blocking_collisions == []
    contextual_entities = {c["entity"] for c in result.contextual_collisions}
    assert {"software.alpha", "software.beta"} <= contextual_entities


def test_collision_detection_blocks_on_effective_auto_replace_override(tmp_path):
    # Entity-level defaults are both auto_replace=False (safe), but one
    # entity overrides this specific alias to auto_replace=True -- the
    # effective policy is unsafe, so this must block even though neither
    # entity's own top-level auto_replace is True.
    entities = [
        make_entity(
            id="software.alpha", canonical="Alpha", ambiguity="medium", auto_replace=False,
            aliases={"ru": [{"value": "shared", "ambiguity": "low", "auto_replace": True}]},
        ),
        make_entity(
            id="software.beta", canonical="Beta", ambiguity="medium", auto_replace=False,
            aliases={"ru": ["shared"]},
        ),
    ]
    write_entities(tmp_path / "data", entities)
    output_path = tmp_path / "gvp.json"
    result = build(tmp_path / "data", REAL_SCHEMA_PATH, output_path)
    assert result.success is False
    assert len(result.blocking_collisions) == 1
    assert not output_path.exists()


# --- Phase 01.1: Wi-Fi / CUDA worked examples against real fixture data ---

def test_wifi_safe_and_risky_aliases_have_different_effective_policies(tmp_path):
    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    wifi_contextual = {
        c["alias"]: c for c in result.contextual_collisions if c["entity"] == "standard.wifi"
    }
    # вайфай is safe -- must NOT appear in the contextual bucket at all.
    assert "вайфай" not in wifi_contextual
    # вафля is the risky, per-alias-overridden one -- must appear, and
    # its effective policy must be the risky one, not the entity default.
    assert wifi_contextual["вафля"]["ambiguity"] == "medium"
    assert wifi_contextual["вафля"]["auto_replace"] is False


def test_old_fixtures_remain_compatible_where_not_migrated(tmp_path):
    # software.cuda.json was deliberately left as a pure Phase 01.0
    # legacy-string-alias entity (no structured aliases) -- it must still
    # build correctly under the 0.2.0 schema and correctly resolve its
    # single alias's effective policy purely via entity-level inheritance.
    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    cuda_contextual = [c for c in result.contextual_collisions if c["entity"] == "software.cuda"]
    assert len(cuda_contextual) == 1
    assert cuda_contextual[0]["alias"] == "куда"
    assert cuda_contextual[0]["ambiguity"] == "high"
    assert cuda_contextual[0]["policy"] == "context_required"
    assert cuda_contextual[0]["auto_replace"] is False


def test_output_retains_structured_alias_metadata(tmp_path):
    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in artifact["entities"]}
    wifi_aliases = by_id["standard.wifi"]["aliases"]["ru"]
    assert "вайфай" in wifi_aliases  # legacy string form preserved as-is
    structured = [a for a in wifi_aliases if isinstance(a, dict)]
    assert len(structured) == 1
    assert structured[0]["value"] == "вафля"
    assert structured[0]["ambiguity"] == "medium"
    assert structured[0]["auto_replace"] is False


def test_deterministic_output_with_structured_aliases_byte_identical(tmp_path):
    out_a = tmp_path / "a" / "gvp.json"
    out_b = tmp_path / "b" / "gvp.json"
    result_a = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, out_a)
    result_b = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, out_b)
    assert result_a.success and result_b.success
    assert out_a.read_bytes() == out_b.read_bytes()
