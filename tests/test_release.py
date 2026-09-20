"""
Phase 02.1 tests for tools/builder/release.py (tag contract, numeric
CalVer comparison, local release-candidate check) and the `release-check`
CLI subcommand.

Same fixture approach as tests/test_package.py: real data/curated/ +
schema for building a genuine package, always into a temp dist-dir.
Phase 02.1 does not talk to GitHub/network at all -- nothing here does
either.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from tools.builder.package import package
from tools.builder.release import (
    ReleaseTagError,
    compare_calver,
    is_valid_release_tag,
    parse_release_tag,
    release_check,
    release_tag,
    release_title,
)
from tools.builder.version import DataPackVersionError, parse_calver_components

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_DATA_DIR = REPO_ROOT / "data" / "curated"
REAL_SCHEMA_PATH = REPO_ROOT / "schema" / "gvp.schema.json"

VALID_VERSION = "2026.09.20.1"
VALID_TAG = "gvp-2026.09.20.1"


# --- tag naming helpers ------------------------------------------------

def test_release_tag_naming():
    assert release_tag(VALID_VERSION) == VALID_TAG


def test_release_title_naming():
    assert release_title(VALID_VERSION) == "EXPC-GVP 2026.09.20.1"


# --- tag parsing / validation -------------------------------------------

def test_valid_gvp_tag_parses():
    assert parse_release_tag(VALID_TAG) == VALID_VERSION
    assert is_valid_release_tag(VALID_TAG) is True


@pytest.mark.parametrize(
    "tag",
    [
        "v2026.09.20.1",  # wrong prefix
        "2026.09.20.1",  # no prefix at all
        "gvp2026.09.20.1",  # missing separator dash
        "GVP-2026.09.20.1",  # prefix is case-sensitive
        "release-2026.09.20.1",  # unrelated repository tag
        "gvp-",  # empty suffix
        "",
    ],
)
def test_malformed_or_non_gvp_tags_rejected(tag):
    with pytest.raises(ReleaseTagError):
        parse_release_tag(tag)
    assert is_valid_release_tag(tag) is False


@pytest.mark.parametrize(
    "tag",
    [
        "gvp-2026.13.20.1",  # month 13
        "gvp-2026.02.30.1",  # not a real calendar date
        "gvp-2026.9.20.1",  # month not zero-padded to 2 digits
        "gvp-2026.09.20.0",  # sequence must be >= 1
        "gvp-not-a-version",
    ],
)
def test_tags_with_invalid_calver_suffix_rejected(tag):
    with pytest.raises(ReleaseTagError):
        parse_release_tag(tag)
    assert is_valid_release_tag(tag) is False


# --- numeric CalVer comparison -------------------------------------------

def test_numeric_calver_comparison_not_lexical():
    # Lexically "2026.09.20.10" < "2026.09.20.9" (since '1' < '9'), but
    # 10 > 9 numerically -- this is exactly the bug a naive string
    # comparison would introduce for a multi-digit sequence number.
    assert compare_calver("2026.09.20.10", "2026.09.20.9") == 1
    assert compare_calver("2026.09.20.9", "2026.09.20.10") == -1
    assert sorted(
        ["2026.09.20.10", "2026.09.20.9", "2026.09.20.2"],
        key=parse_calver_components,
    ) == ["2026.09.20.2", "2026.09.20.9", "2026.09.20.10"]


def test_numeric_calver_comparison_across_dates():
    assert compare_calver("2026.10.01.1", "2026.09.30.9") == 1
    assert compare_calver("2026.09.30.9", "2026.10.01.1") == -1


def test_calver_comparison_equal():
    assert compare_calver(VALID_VERSION, VALID_VERSION) == 0


def test_calver_comparison_rejects_invalid_input():
    with pytest.raises(DataPackVersionError):
        compare_calver("not-a-version", VALID_VERSION)


# --- local release-candidate check ---------------------------------------

def test_valid_release_candidate_passes(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success

    check = release_check(VALID_TAG, result.package_dir)
    assert check.success is True
    assert check.errors == []
    assert check.data_pack_version == VALID_VERSION


def test_release_check_rejects_malformed_tag(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success

    check = release_check("v2026.09.20.1", result.package_dir)
    assert check.success is False
    assert any("invalid GVP release tag" in e for e in check.errors)


def test_release_check_rejects_tag_manifest_version_mismatch(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success

    check = release_check("gvp-2026.09.20.2", result.package_dir)
    assert check.success is False
    assert any("does not match manifest" in e for e in check.errors)


def test_release_check_rejects_missing_asset(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    (result.package_dir / "checksums.sha256").unlink()

    check = release_check(VALID_TAG, result.package_dir)
    assert check.success is False
    assert any("missing required file" in e for e in check.errors)


def test_release_check_rejects_tampered_package(tmp_path):
    result = package(REAL_DATA_DIR, REAL_SCHEMA_PATH, tmp_path, VALID_VERSION)
    assert result.success
    gvp_path = result.package_dir / "gvp.json"
    gvp_path.write_bytes(gvp_path.read_bytes() + b" ")

    check = release_check(VALID_TAG, result.package_dir)
    assert check.success is False
    assert any("SHA-256 mismatch" in e for e in check.errors)
    # Rejected via the *existing* verification engine, not a second one.
    assert check.verify_result is not None
    assert check.verify_result.success is False


def test_release_check_nonexistent_package_dir(tmp_path):
    check = release_check(VALID_TAG, tmp_path / "does-not-exist")
    assert check.success is False
    assert any("missing required file" in e for e in check.errors)


# --- CLI -------------------------------------------------------------------

def _run_cli(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "tools.builder", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_release_check_cli_success_exit_code(tmp_path):
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

    proc = _run_cli(
        ["release-check", "--tag", VALID_TAG, str(tmp_path / VALID_VERSION)],
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RELEASE-CHECK: PASS" in proc.stdout


def test_release_check_cli_failure_exit_code_bad_tag(tmp_path):
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

    proc = _run_cli(
        ["release-check", "--tag", "gvp-2026.09.20.999", str(tmp_path / VALID_VERSION)],
        cwd=REPO_ROOT,
    )
    assert proc.returncode != 0
    assert "RELEASE-CHECK: FAIL" in proc.stdout
