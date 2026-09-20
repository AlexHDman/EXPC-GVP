"""
Phase 02.0 tests for tools/builder/package.py, verify.py, manifest.py,
and checksums.py, plus the `package`/`verify` CLI subcommands.

Mirrors tests/test_builder.py's approach: synthetic temp-directory
fixtures for failure-path scenarios, real data/curated/ + schema for
success-path/behavioral assertions, and always packaging to a temp
dist-dir, never the real dist/, so running the suite never mutates the
real Data Pack.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from tools.builder.checksums import parse_checksums
from tools.builder.manifest import MANIFEST_CONTRACT_VERSION
from tools.builder.package import package
from tools.builder.verify import verify_package

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_DATA_DIR = REPO_ROOT / "data" / "curated"
REAL_SCHEMA_PATH = REPO_ROOT / "schema" / "gvp.schema.json"

VALID_VERSION = "2026.09.20.1"


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
        path.write_text(json.dumps(entity, ensure_ascii=False), encoding="utf-8")
    return data_dir


# --- successful packaging against the real fixture dataset -----------------

def test_package_created_successfully(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success is True
    assert not result.errors
    assert result.package_dir == tmp_path / VALID_VERSION


def test_expected_three_files_exist(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    names = {p.name for p in result.package_dir.iterdir()}
    assert names == {"gvp.json", "manifest.json", "checksums.sha256"}


def test_manifest_contract_correct(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    manifest = json.loads((result.package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_contract_version"] == MANIFEST_CONTRACT_VERSION
    assert manifest["project"] == "EXPC-GVP"
    assert manifest["data_pack_version"] == VALID_VERSION
    assert manifest["schema_version"] == "0.2.0"
    assert manifest["builder_version"] == result.builder_version
    assert manifest["entity_count"] == 15
    assert manifest["artifact"]["filename"] == "gvp.json"
    assert manifest["artifact"]["sha256"] == result.artifact_sha256
    # No volatile/local-machine fields.
    assert "timestamp" not in manifest
    assert "built_at" not in manifest
    dumped = json.dumps(manifest)
    assert str(tmp_path) not in dumped  # no absolute local path leaked in


def test_artifact_sha256_correct(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    gvp_bytes = (result.package_dir / "gvp.json").read_bytes()
    assert hashlib.sha256(gvp_bytes).hexdigest() == result.artifact_sha256
    manifest = json.loads((result.package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifact"]["sha256"] == result.artifact_sha256


def test_artifact_byte_size_correct(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    gvp_bytes = (result.package_dir / "gvp.json").read_bytes()
    manifest = json.loads((result.package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifact"]["size_bytes"] == len(gvp_bytes)


def test_entity_count_correct(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    gvp_data = json.loads((result.package_dir / "gvp.json").read_text(encoding="utf-8"))
    manifest = json.loads((result.package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["entity_count"] == len(gvp_data["entities"]) == 15


def test_checksums_file_correct(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    checksums_text = (result.package_dir / "checksums.sha256").read_text(encoding="utf-8")
    parsed = parse_checksums(checksums_text)
    assert set(parsed) == {"gvp.json", "manifest.json"}  # never itself
    gvp_bytes = (result.package_dir / "gvp.json").read_bytes()
    manifest_bytes = (result.package_dir / "manifest.json").read_bytes()
    assert parsed["gvp.json"] == hashlib.sha256(gvp_bytes).hexdigest()
    assert parsed["manifest.json"] == hashlib.sha256(manifest_bytes).hexdigest()
    # Conventional sha256sum two-space format.
    first_line = checksums_text.splitlines()[0]
    assert "  " in first_line
    assert len(first_line.split("  ")[0]) == 64  # hex sha256 length


# --- version validation ----------------------------------------------------

def test_package_rejects_invalid_calver(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, "not-a-version")
    assert result.success is False
    assert result.errors
    assert not (tmp_path / "not-a-version").exists()


def test_package_propagates_build_failure(tmp_path):
    bad_entities = [make_entity(ambiguity="not-a-real-level")]
    data_dir = write_entities(tmp_path / "data", bad_entities)
    result = package(data_dir, REAL_SCHEMA_PATH, tmp_path / "dist", VALID_VERSION)
    assert result.success is False
    assert result.errors
    assert not (tmp_path / "dist" / VALID_VERSION).exists()


# --- verification: valid package -------------------------------------------

def test_verify_valid_package_passes(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    verify_result = verify_package(result.package_dir)
    assert verify_result.success is True
    assert verify_result.errors == []
    assert verify_result.manifest["data_pack_version"] == VALID_VERSION


def test_verify_missing_file_fails(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    (result.package_dir / "checksums.sha256").unlink()
    verify_result = verify_package(result.package_dir)
    assert verify_result.success is False
    assert any("missing required file" in e for e in verify_result.errors)


def test_verify_tampered_gvp_json_fails(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    gvp_path = result.package_dir / "gvp.json"
    gvp_path.write_bytes(gvp_path.read_bytes() + b" ")
    verify_result = verify_package(result.package_dir)
    assert verify_result.success is False
    assert any("SHA-256 mismatch" in e for e in verify_result.errors)


def test_verify_tampered_manifest_fails(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    manifest_path = result.package_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["entity_count"] = 999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    verify_result = verify_package(result.package_dir)
    assert verify_result.success is False
    # manifest.json's own bytes changed, so checksums.sha256 no longer
    # matches it -- and the tampered entity_count itself disagrees with
    # gvp.json too.
    assert any("checksums.sha256 mismatch for manifest.json" in e for e in verify_result.errors)
    assert any("entity_count mismatch" in e for e in verify_result.errors)


def test_verify_tampered_checksums_fails(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    checksums_path = result.package_dir / "checksums.sha256"
    checksums_path.write_text(
        "0000000000000000000000000000000000000000000000000000000000000000  gvp.json\n",
        encoding="utf-8",
    )
    verify_result = verify_package(result.package_dir)
    assert verify_result.success is False
    assert any("checksums.sha256 mismatch" in e for e in verify_result.errors)


def test_verify_unsupported_manifest_contract_fails(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    manifest_path = result.package_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["manifest_contract_version"] = "99.0"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    verify_result = verify_package(result.package_dir)
    assert verify_result.success is False
    assert any("unsupported manifest_contract_version" in e for e in verify_result.errors)


# --- determinism -------------------------------------------------------

def test_two_independent_package_builds_are_byte_identical(tmp_path):
    result_a = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path / "dist_a", VALID_VERSION)
    result_b = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path / "dist_b", VALID_VERSION)
    assert result_a.success and result_b.success
    for filename in ("gvp.json", "manifest.json", "checksums.sha256"):
        bytes_a = (result_a.package_dir / filename).read_bytes()
        bytes_b = (result_b.package_dir / filename).read_bytes()
        assert bytes_a == bytes_b, f"{filename} differs between independent builds"


def test_repackaging_same_version_same_data_is_idempotent_noop(tmp_path):
    result_1 = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result_1.success and result_1.reused_existing is False
    original_bytes = {
        f: (result_1.package_dir / f).read_bytes()
        for f in ("gvp.json", "manifest.json", "checksums.sha256")
    }

    result_2 = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result_2.success and result_2.reused_existing is True
    for f, data in original_bytes.items():
        assert (result_2.package_dir / f).read_bytes() == data


# --- safe / atomic packaging --------------------------------------------

def test_failed_repackage_preserves_previous_valid_package(tmp_path):
    good_result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert good_result.success
    original_bytes = {
        f: (good_result.package_dir / f).read_bytes()
        for f in ("gvp.json", "manifest.json", "checksums.sha256")
    }

    # Different source data under the SAME version -- must be refused,
    # and must not touch the already-published package.
    different_entities = [make_entity(canonical="SomethingElse")]
    bad_data_dir = write_entities(tmp_path / "other_data", different_entities)
    bad_result = package(bad_data_dir, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert bad_result.success is False

    for f, data in original_bytes.items():
        assert (good_result.package_dir / f).read_bytes() == data


def test_no_staging_directories_left_after_success_or_failure(tmp_path):
    package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)

    bad_entities = [make_entity(ambiguity="not-a-real-level")]
    bad_data_dir = write_entities(tmp_path / "bad_data", bad_entities)
    package(bad_data_dir, REAL_SCHEMA_PATH, tmp_path, "2026.09.20.2")

    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(".pkg-staging-")]
    assert leftovers == []


# --- existing build command unaffected ----------------------------------

def test_build_command_still_works(tmp_path):
    from tools.builder.build import build

    output_path = tmp_path / "gvp.json"
    result = build(REAL_DATA_DIR, REAL_SCHEMA_PATH, output_path)
    assert result.success is True
    assert output_path.exists()


# --- CLI -----------------------------------------------------------------

def _run_cli(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "tools.builder", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_package_cli_success_exit_code(tmp_path):
    proc = _run_cli(
        [
            "package", "--version", VALID_VERSION,
            "--data-dir", str(REAL_DATA_DIR),
            "--schema", str(REAL_SCHEMA_PATH),
            "--dist-dir", str(tmp_path),
        ],
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PACKAGE: PASS" in proc.stdout
    assert (tmp_path / VALID_VERSION / "gvp.json").exists()


def test_package_cli_failure_exit_code_invalid_version(tmp_path):
    proc = _run_cli(
        [
            "package", "--version", "bogus",
            "--data-dir", str(REAL_DATA_DIR),
            "--schema", str(REAL_SCHEMA_PATH),
            "--dist-dir", str(tmp_path),
        ],
        cwd=REPO_ROOT,
    )
    assert proc.returncode != 0
    assert "PACKAGE: FAIL" in proc.stdout


def test_verify_cli_success_exit_code(tmp_path):
    pkg_proc = _run_cli(
        [
            "package", "--version", VALID_VERSION,
            "--data-dir", str(REAL_DATA_DIR),
            "--schema", str(REAL_SCHEMA_PATH),
            "--dist-dir", str(tmp_path),
        ],
        cwd=REPO_ROOT,
    )
    assert pkg_proc.returncode == 0

    verify_proc = _run_cli(["verify", str(tmp_path / VALID_VERSION)], cwd=REPO_ROOT)
    assert verify_proc.returncode == 0, verify_proc.stdout + verify_proc.stderr
    assert "VERIFY: PASS" in verify_proc.stdout


def test_verify_cli_failure_exit_code(tmp_path):
    proc = _run_cli(["verify", str(tmp_path / "does-not-exist")], cwd=REPO_ROOT)
    assert proc.returncode != 0
    assert "VERIFY: FAIL" in proc.stdout
