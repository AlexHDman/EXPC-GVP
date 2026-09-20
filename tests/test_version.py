"""
Phase 02.0 tests for tools/builder/version.py: Data Pack CalVer validation.
"""
import pytest

from tools.builder.version import DataPackVersionError, validate_data_pack_version


@pytest.mark.parametrize(
    "version",
    [
        "2026.09.20.1",
        "2026.01.01.1",
        "2026.12.31.1",
        "2026.09.20.42",  # multi-digit sequence
        "1999.09.20.1",
    ],
)
def test_valid_calver_accepted(version):
    validate_data_pack_version(version)  # must not raise


@pytest.mark.parametrize(
    "version",
    [
        "2026-09-20",          # wrong separators
        "2026.09.20",          # missing sequence number
        "2026.9.20.1",         # month not zero-padded
        "2026.09.2.1",         # day not zero-padded
        "26.09.20.1",          # 2-digit year
        "2026.13.20.1",        # invalid month
        "2026.02.30.1",        # invalid day for February
        "2026.09.20.0",        # sequence must be >= 1
        "2026.09.20.-1",       # negative sequence
        "v2026.09.20.1",       # extraneous prefix
        "2026.09.20.1 ",       # trailing whitespace
        "",                    # empty
    ],
)
def test_invalid_versions_rejected(version):
    with pytest.raises(DataPackVersionError):
        validate_data_pack_version(version)


def test_non_string_rejected():
    with pytest.raises(DataPackVersionError):
        validate_data_pack_version(20260920.1)  # type: ignore[arg-type]
