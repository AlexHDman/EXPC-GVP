"""
Phase 01.0 tests for the EXPC-GVP Builder (tools/builder/).

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
