"""
Data Pack packaging (Phase 02.0): builds dist/<data_pack_version>/
containing gvp.json + manifest.json + checksums.sha256.

Reuses the existing Builder validation pipeline (tools/builder/build.py:
assemble_artifact) instead of re-implementing schema/semantic/collision
checks -- packaging is purely "take an already-valid artifact and wrap it
with distribution metadata", not a second data pipeline.

See docs/05_DISTRIBUTION.md for the package layout, manifest contract,
and checksum model this implements, and _stage_and_publish's docstring
below for the Windows-safe atomic-publish strategy (STEP 7).
"""
import hashlib
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from . import __builder_version__
from .build import assemble_artifact
from .checksums import format_checksums
from .manifest import build_manifest
from .serialize import serialize_json_deterministic
from .verify import verify_package
from .version import DataPackVersionError, validate_data_pack_version

ARTIFACT_FILENAME = "gvp.json"
MANIFEST_FILENAME = "manifest.json"
CHECKSUMS_FILENAME = "checksums.sha256"


@dataclass
class PackageResult:
    success: bool
    data_pack_version: str = ""
    schema_version: str = ""
    builder_version: str = __builder_version__
    entity_count: int = 0
    artifact_sha256: str = ""
    package_dir: Optional[Path] = None
    reused_existing: bool = False
    errors: List[str] = field(default_factory=list)


class _PublishConflict(Exception):
    pass


def package(
    data_dir: Path, schema_path: Path, dist_dir: Path, data_pack_version: str
) -> PackageResult:
    result = PackageResult(success=False, data_pack_version=data_pack_version)

    try:
        validate_data_pack_version(data_pack_version)
    except DataPackVersionError as e:
        result.errors.append(str(e))
        return result

    build_result = assemble_artifact(Path(data_dir), Path(schema_path))
    result.schema_version = build_result.schema_version
    result.entity_count = build_result.entity_count

    if not build_result.success:
        result.errors.extend(build_result.schema_errors)
        result.errors.extend(build_result.semantic_errors)
        if build_result.blocking_collisions:
            result.errors.append(
                f"{len(build_result.blocking_collisions)} blocking collision(s) -- see build output"
            )
        return result

    gvp_bytes = serialize_json_deterministic(build_result.artifact)
    gvp_sha256 = hashlib.sha256(gvp_bytes).hexdigest()
    result.artifact_sha256 = gvp_sha256

    manifest = build_manifest(
        data_pack_version=data_pack_version,
        schema_version=build_result.schema_version,
        builder_version=__builder_version__,
        entity_count=build_result.entity_count,
        artifact_filename=ARTIFACT_FILENAME,
        artifact_sha256=gvp_sha256,
        artifact_size_bytes=len(gvp_bytes),
    )
    manifest_bytes = serialize_json_deterministic(manifest)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    checksums_bytes = format_checksums(
        {ARTIFACT_FILENAME: gvp_sha256, MANIFEST_FILENAME: manifest_sha256}
    ).encode("utf-8")

    dist_dir = Path(dist_dir)
    final_dir = dist_dir / data_pack_version

    try:
        package_dir, reused = _stage_and_publish(
            dist_dir,
            final_dir,
            {
                ARTIFACT_FILENAME: gvp_bytes,
                MANIFEST_FILENAME: manifest_bytes,
                CHECKSUMS_FILENAME: checksums_bytes,
            },
        )
    except _PublishConflict as e:
        result.errors.append(str(e))
        return result

    result.success = True
    result.package_dir = package_dir
    result.reused_existing = reused
    return result


def _stage_and_publish(dist_dir: Path, final_dir: Path, files: Dict[str, bytes]):
    """
    Staging/temp -> self-verify -> atomic publish. `files` maps filename
    -> bytes for every file the package must contain.

    Windows directory-replace note: an atomic rename (os.replace /
    Path.replace) can move a directory into a path that does not yet
    exist, but Windows -- unlike POSIX for an *empty* destination
    directory -- cannot atomically replace an existing, non-empty
    destination directory in one filesystem operation. Rather than trying
    to emulate a cross-platform transactional directory replace (which
    the brief explicitly says not to over-engineer), this treats a Data
    Pack version as immutable once published:

      - final_dir does not exist yet -> plain atomic rename of the
        staging directory into place. The common case.
      - final_dir already exists and its 3 files are byte-identical to
        the freshly-staged ones -> harmless no-op (e.g. re-running
        `package` for the same version against unchanged source data).
        The existing directory is left completely untouched; only the
        disposable staging directory is removed.
      - final_dir already exists with DIFFERENT content -> that is a
        genuine version-immutability violation (the same CalVer version
        string would otherwise point at two different datasets). This
        fails loudly and leaves the existing, previously-valid package
        completely untouched -- exactly the "existing valid package of
        that version must not be corrupted" requirement.

    Returns (final_dir, reused_existing: bool).
    """
    dist_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = dist_dir / f".pkg-staging-{uuid.uuid4().hex}"
    staging_dir.mkdir()
    try:
        for filename, data in files.items():
            (staging_dir / filename).write_bytes(data)

        verify_result = verify_package(staging_dir)
        if not verify_result.success:
            # Should be unreachable in practice -- a self-check that the
            # package this module just built is internally consistent.
            raise _PublishConflict(
                f"internal error: freshly-built package failed self-verification: "
                f"{verify_result.errors}"
            )

        if final_dir.exists():
            if _directory_contents_match(staging_dir, final_dir, files.keys()):
                return final_dir, True
            raise _PublishConflict(
                f"{final_dir} already exists with DIFFERENT content -- Data Pack "
                f"versions are immutable once published; use a new version "
                f"(bump the CalVer sequence number) instead of overwriting "
                f"'{final_dir.name}'"
            )

        staging_dir.replace(final_dir)
        return final_dir, False
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def _directory_contents_match(dir_a: Path, dir_b: Path, filenames) -> bool:
    for filename in filenames:
        b_path = dir_b / filename
        if not b_path.is_file():
            return False
        if (dir_a / filename).read_bytes() != b_path.read_bytes():
            return False
    return True
