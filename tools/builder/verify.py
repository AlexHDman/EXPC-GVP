"""
Package verification (Phase 02.0): validates a produced dist/<version>/
package directory in isolation -- from its own files only, without
rebuilding from data/curated/ or needing the schema at all.

This is deliberately reusable by a future updater/consumer (per the
Phase 02.0 brief) as a standalone integrity check: given nothing but a
package directory, is it internally self-consistent? It does not fetch,
download, install, or compare against any other version -- no network
access, no WLK integration (Phase 02.0 scope guard).
"""
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .checksums import parse_checksums
from .manifest import MANIFEST_CONTRACT_VERSION

REQUIRED_FILES = ("gvp.json", "manifest.json", "checksums.sha256")
SUPPORTED_MANIFEST_CONTRACT_VERSIONS = {MANIFEST_CONTRACT_VERSION}


@dataclass
class VerifyResult:
    success: bool
    package_dir: Path
    errors: List[str] = field(default_factory=list)
    manifest: Optional[dict] = None


def verify_package(package_dir: Path) -> VerifyResult:
    package_dir = Path(package_dir)
    result = VerifyResult(success=False, package_dir=package_dir)

    # 1. Required files exist.
    missing = [f for f in REQUIRED_FILES if not (package_dir / f).is_file()]
    if missing:
        result.errors.append(f"missing required file(s): {missing}")
        return result

    gvp_bytes = (package_dir / "gvp.json").read_bytes()
    manifest_bytes = (package_dir / "manifest.json").read_bytes()
    checksums_text = (package_dir / "checksums.sha256").read_text(encoding="utf-8")

    # 2. manifest.json parses.
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as e:
        result.errors.append(f"manifest.json is not valid JSON: {e}")
        return result
    result.manifest = manifest

    # 3. Supported manifest contract.
    contract_version = manifest.get("manifest_contract_version")
    if contract_version not in SUPPORTED_MANIFEST_CONTRACT_VERSIONS:
        result.errors.append(
            f"unsupported manifest_contract_version {contract_version!r} "
            f"(supported: {sorted(SUPPORTED_MANIFEST_CONTRACT_VERSIONS)})"
        )
        return result

    artifact_meta = manifest.get("artifact", {})

    # 4. Artifact SHA-256 matches.
    actual_sha256 = hashlib.sha256(gvp_bytes).hexdigest()
    expected_sha256 = artifact_meta.get("sha256")
    if actual_sha256 != expected_sha256:
        result.errors.append(
            f"gvp.json SHA-256 mismatch: manifest says {expected_sha256!r}, "
            f"actual is {actual_sha256!r}"
        )

    # 5. Artifact byte size matches.
    actual_size = len(gvp_bytes)
    expected_size = artifact_meta.get("size_bytes")
    if actual_size != expected_size:
        result.errors.append(
            f"gvp.json size mismatch: manifest says {expected_size!r}, "
            f"actual is {actual_size!r}"
        )

    # 6 + 7. gvp.json parses; entity count and schema version coherence.
    try:
        gvp_data = json.loads(gvp_bytes)
    except json.JSONDecodeError as e:
        result.errors.append(f"gvp.json is not valid JSON: {e}")
        gvp_data = None

    if gvp_data is not None:
        actual_entity_count = len(gvp_data.get("entities", []))
        expected_entity_count = manifest.get("entity_count")
        if actual_entity_count != expected_entity_count:
            result.errors.append(
                f"entity_count mismatch: manifest says {expected_entity_count!r}, "
                f"gvp.json has {actual_entity_count!r}"
            )

        gvp_schema_version = gvp_data.get("schema_version")
        manifest_schema_version = manifest.get("schema_version")
        if gvp_schema_version != manifest_schema_version:
            result.errors.append(
                f"schema_version mismatch: manifest says {manifest_schema_version!r}, "
                f"gvp.json says {gvp_schema_version!r}"
            )

    # 8. checksums.sha256 matches the actual files it covers.
    expected_checksums = parse_checksums(checksums_text)
    actual_checksums = {
        "gvp.json": actual_sha256,
        "manifest.json": hashlib.sha256(manifest_bytes).hexdigest(),
    }
    for filename, actual_hash in actual_checksums.items():
        expected_hash = expected_checksums.get(filename)
        if expected_hash != actual_hash:
            result.errors.append(
                f"checksums.sha256 mismatch for {filename}: file says "
                f"{expected_hash!r}, actual is {actual_hash!r}"
            )
    unexpected = set(expected_checksums) - set(actual_checksums)
    if unexpected:
        result.errors.append(f"checksums.sha256 lists unexpected file(s): {sorted(unexpected)}")

    result.success = not result.errors
    return result
