"""
Builder pipeline orchestration (Phase 01.0 MVP):

    data/curated/*.json
            |
        load                          (loader.py)
            |
    JSON Schema validation            (validator.py: validate_schema_conformance)
            |
    semantic validation               (validator.py: validate_semantics)
            |
    normalization for comparison      (normalize.py, used by the stages above/below)
            |
    collision analysis                (collisions.py)
            |
    deterministic build artifact      (this module: _write_artifact_atomically)

Mirrors docs/00_ARCHITECTURE.md's conceptual pipeline diagram, scoped down
to what Phase 01.0 actually implements (no dedup/canonicalization/source
validation stages yet -- those require sources this repo does not have).

Every stage after the first failing one is skipped, and dist/gvp.json is
only ever written once every stage has passed with zero blocking issues.
"""
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import loader
from . import validator as validator_mod
from .collisions import analyze_collisions


@dataclass
class BuildResult:
    success: bool
    entity_count: int = 0
    schema_version: str = ""
    schema_errors: List[str] = field(default_factory=list)
    semantic_errors: List[str] = field(default_factory=list)
    blocking_collisions: List[dict] = field(default_factory=list)
    contextual_collisions: List[dict] = field(default_factory=list)
    output_path: Optional[Path] = None
    wrote_output: bool = False


def build(data_dir: Path, schema_path: Path, output_path: Path) -> BuildResult:
    data_dir = Path(data_dir)
    schema_path = Path(schema_path)
    output_path = Path(output_path)

    schema = validator_mod.load_schema(schema_path)
    jsonschema_validator = validator_mod.make_validator(schema)
    schema_version = schema.get("x-schema-version", "unknown")

    paths = loader.find_entity_paths(data_dir)
    loaded = loader.load_entities(paths)

    result = BuildResult(
        success=False,
        entity_count=len(loaded),
        schema_version=schema_version,
        output_path=output_path,
    )

    if not loaded:
        result.semantic_errors.append(f"no entity files found in {data_dir}")
        return result

    # Stage: JSON Schema validation.
    schema_errors: List[str] = []
    for path, data in loaded:
        schema_errors.extend(
            validator_mod.validate_schema_conformance(jsonschema_validator, path, data)
        )
    result.schema_errors = schema_errors
    if schema_errors:
        return result

    # Stage: semantic validation (cross-record / runtime contract).
    semantic_errors = validator_mod.validate_semantics(loaded)
    result.semantic_errors = semantic_errors
    if semantic_errors:
        return result

    # Stage: collision analysis (uses normalization internally).
    entities = [data for _, data in loaded]
    blocking, contextual = analyze_collisions(entities)
    result.blocking_collisions = blocking
    result.contextual_collisions = contextual
    if blocking:
        return result

    # Stage: deterministic build artifact.
    entities_sorted = sorted(entities, key=lambda e: e["id"])
    artifact = {
        "schema_version": schema_version,
        "entity_count": len(entities_sorted),
        "entities": entities_sorted,
    }
    _write_artifact_atomically(output_path, artifact)

    result.success = True
    result.wrote_output = True
    return result


def _write_artifact_atomically(output_path: Path, artifact: dict) -> None:
    """
    Staging/temp -> atomic replace, so a crash or error mid-write can
    never leave a truncated/corrupt dist/gvp.json, and a previously
    valid artifact is never touched unless the new one fully succeeded.

    The temp file is created in the *same directory* as output_path so
    os.replace() is an atomic rename on the same filesystem/volume.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".gvp-build-", suffix=".tmp", dir=str(output_path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(artifact, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, output_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
