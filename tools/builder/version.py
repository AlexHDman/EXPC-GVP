"""
Data Pack version: CalVer, format YYYY.MM.DD.N (e.g. "2026.09.20.1").

Deliberately does NOT auto-generate "today's" version, auto-increment a
sequence number, or scan any external source (filesystem history, GitHub,
a network endpoint) to pick one. Per the Phase 02.0 scope guard, a Data
Pack version is always an explicit input (CLI `--version`) that this
module only validates -- never inferred, so packaging stays fully
deterministic and independent of the wall clock or network access. This
is also *the* one clear version source the brief asks for: a curator (or
future automation) decides the version string and passes it in; this
module is the single place that decides whether that string is
well-formed.
"""
import re
from datetime import date

CALVER_PATTERN = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})\.(\d+)$")


class DataPackVersionError(ValueError):
    pass


def validate_data_pack_version(version: str) -> None:
    """
    Raises DataPackVersionError if `version` is not a well-formed CalVer
    Data Pack version. Checks: overall YYYY.MM.DD.N shape, that
    YYYY-MM-DD is a real calendar date (rejects e.g. month 13 or Feb 30
    via `datetime.date`, not just digit-count matching), and that the
    trailing sequence number N is a positive integer (>= 1).
    """
    if not isinstance(version, str):
        raise DataPackVersionError(f"Data Pack version must be a string, got {type(version).__name__}")

    match = CALVER_PATTERN.match(version)
    if not match:
        raise DataPackVersionError(
            f"invalid Data Pack version {version!r}: expected CalVer format "
            f"YYYY.MM.DD.N (e.g. '2026.09.20.1')"
        )

    year, month, day, sequence = match.groups()
    try:
        date(int(year), int(month), int(day))
    except ValueError as e:
        raise DataPackVersionError(
            f"invalid Data Pack version {version!r}: {year}-{month}-{day} is not a real calendar date ({e})"
        ) from e

    if int(sequence) < 1:
        raise DataPackVersionError(
            f"invalid Data Pack version {version!r}: sequence number must be >= 1, got {sequence}"
        )


def parse_calver_components(version: str) -> tuple:
    """
    Validates `version` (via `validate_data_pack_version`) and returns its
    (year, month, day, sequence) as a tuple of ints, for *numeric* CalVer
    comparison. Callers must not compare Data Pack version strings
    lexically: the sequence number `N` has no fixed width (`\\d+`), so e.g.
    "2026.09.20.10" < "2026.09.20.9" as strings even though 10 > 9
    numerically. Comparing the tuples this returns instead gives the
    correct ordering.
    """
    validate_data_pack_version(version)
    match = CALVER_PATTERN.match(version)
    year, month, day, sequence = match.groups()
    return (int(year), int(month), int(day), int(sequence))
