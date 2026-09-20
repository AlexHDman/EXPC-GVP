"""
GitHub Release *contract* (Phase 02.1): pure, local, offline logic for the
tag/version naming convention and for validating a local package directory
as a release candidate for a given tag.

Deliberately thin: this module does not talk to GitHub, does not create
tags or releases, and does not implement release discovery over a
network. It gives that future logic something deterministic and testable
to call -- `parse_release_tag`/`is_valid_release_tag` for filtering tags,
`compare_calver` for ordering them, and `release_check` for the one new
piece of local validation Phase 02.1 actually adds. `release_check`
itself is orchestration only: it re-uses `verify.py: verify_package` for
every integrity/tamper check rather than re-implementing any of them --
see docs/06_RELEASE_CONTRACT.md.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .verify import VerifyResult, verify_package
from .version import DataPackVersionError, parse_calver_components

TAG_PREFIX = "gvp-"


class ReleaseTagError(ValueError):
    pass


def release_tag(data_pack_version: str) -> str:
    """Data Pack CalVer -> the Git tag that names its GitHub Release."""
    return f"{TAG_PREFIX}{data_pack_version}"


def release_title(data_pack_version: str) -> str:
    """Data Pack CalVer -> the GitHub Release title."""
    return f"EXPC-GVP {data_pack_version}"


def parse_release_tag(tag: str) -> str:
    """
    Validates `tag` against the Phase 02.1 tag contract (exactly
    `gvp-<CalVer>`, where `<CalVer>` is a well-formed Data Pack version)
    and returns the CalVer portion. Raises ReleaseTagError for anything
    else -- wrong/missing prefix, or a suffix that isn't a valid CalVer --
    so a future discovery loop can catch this one exception type and skip
    the tag, per "malformed/non-GVP tags must be ignored".
    """
    if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
        raise ReleaseTagError(
            f"invalid GVP release tag {tag!r}: must start with {TAG_PREFIX!r}"
        )

    version = tag[len(TAG_PREFIX):]
    try:
        parse_calver_components(version)
    except DataPackVersionError as e:
        raise ReleaseTagError(f"invalid GVP release tag {tag!r}: {e}") from e

    return version


def is_valid_release_tag(tag: str) -> bool:
    """Non-raising convenience wrapper for filtering a list of tags."""
    try:
        parse_release_tag(tag)
        return True
    except ReleaseTagError:
        return False


def compare_calver(a: str, b: str) -> int:
    """
    Numeric CalVer comparison: -1 if `a` < `b`, 0 if equal, 1 if `a` > `b`.
    Both must already be well-formed Data Pack versions (raises
    DataPackVersionError otherwise). Never compares the strings lexically
    -- see `version.py: parse_calver_components` for why that would be
    wrong for a multi-digit sequence number.
    """
    ka = parse_calver_components(a)
    kb = parse_calver_components(b)
    if ka < kb:
        return -1
    if ka > kb:
        return 1
    return 0


@dataclass
class ReleaseCheckResult:
    success: bool
    tag: str
    package_dir: Path
    data_pack_version: str = ""
    errors: List[str] = field(default_factory=list)
    verify_result: Optional[VerifyResult] = None


def release_check(tag: str, package_dir: Path) -> ReleaseCheckResult:
    """
    Local-only release-candidate validation for `tag` against the package
    directory `package_dir` -- no GitHub API, no network. Checks, in
    order (stops at the first failure):

      1. `tag` matches the `gvp-<CalVer>` contract (`parse_release_tag`).
      2. The package passes full standalone verification
         (`verify.py: verify_package` -- this alone covers "all three
         required files present", every integrity/tamper check, and the
         manifest-contract check).
      3. `tag`'s CalVer exactly equals the verified manifest's
         `data_pack_version` -- the tag must name the exact package it is
         attached to, not merely *a* valid one.
    """
    package_dir = Path(package_dir)
    result = ReleaseCheckResult(success=False, tag=tag, package_dir=package_dir)

    try:
        tag_version = parse_release_tag(tag)
    except ReleaseTagError as e:
        result.errors.append(str(e))
        return result
    result.data_pack_version = tag_version

    verify_result = verify_package(package_dir)
    result.verify_result = verify_result
    if not verify_result.success:
        result.errors.extend(verify_result.errors)
        return result

    manifest_version = verify_result.manifest.get("data_pack_version")
    if manifest_version != tag_version:
        result.errors.append(
            f"tag CalVer {tag_version!r} does not match manifest "
            f"data_pack_version {manifest_version!r}"
        )
        return result

    result.success = True
    return result
