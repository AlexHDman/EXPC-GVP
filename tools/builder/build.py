"""
Builder pipeline orchestration (Phase 01.0 MVP, extended in 01.1 and 02.0):

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
    collision analysis                (collisions.py, alias-level since Phase 01.1
                                        via policy.py's effective-policy resolution)
            |
    in-memory artifact                (assemble_artifact, below)
            |
    deterministic write               (build(): dist/gvp.json  |  package.py: dist/<version>/gvp.json)

Mirrors docs/00_ARCHITECTURE.md's conceptual pipeline diagram, scoped down
to what Phase 01.0/01.1/02.0 actually implement (no dedup/canonicalization/
source validation stages yet -- those require sources this repo does not
have).

Every stage after the first failing one is skipped. `assemble_artifact`
does validation/analysis only and never touches the filesystem for
output -- `build()` is the thin wrapper that also writes dist/gvp.json,
and `tools/builder/package.py` reuses `assemble_artifact` directly to
build the same artifact bytes for a versioned Data Pack, so the
validation pipeline is never duplicated between the two.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import loader
from . import validator as validator_mod
from .atomic_write import write_bytes_atomically
from .collisions import analyze_collisions
from .serialize import serialize_json_deterministic


@dataclass
class BuildResult:
    success: bool
    entity_count: int = 0
    schema_version: str = ""
    schema_errors: List[str] = field(default_factory=list)
    semantic_errors: List[str] = field(default_factory=list)
    blocking_collisions: List[dict] = field(default_factory=list)
    contextual_collisions: List[dict] = field(default_factory=list)
    artifact: Optional[dict] = None
    output_path: Optional[Path] = None
    wrote_output: bool = False


def assemble_artifact(data_dir: Path, schema_path: Path) -> BuildResult:
    """
    Runs load -> schema validation -> semantic validation -> collision
    analysis, and on success populates `result.artifact` with the same
    dict `build()` would write to dist/gvp.json -- without writing
    anything to disk. `result.output_path`/`result.wrote_output` are left
    at their defaults; only `build()` (or another caller that goes on to
    write the artifact itself) sets those.
    """
    data_dir = Path(data_dir)
    schema_path = Path(schema_path)

    schema = validator_mod.load_schema(schema_path)
    jsonschema_validator = validator_mod.make_validator(schema)
    schema_version = schema.get("x-schema-version", "unknown")

    paths = loader.find_entity_paths(data_dir)
    loaded = loader.load_entities(paths)

    result = BuildResult(
        success=False,
        entity_count=len(loaded),
        schema_version=schema_version,
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

    # Stage: deterministic in-memory artifact.
    entities_sorted = sorted(entities, key=lambda e: e["id"])
    result.artifact = {
        "schema_version": schema_version,
        "entity_count": len(entities_sorted),
        "entities": entities_sorted,
    }
    result.success = True
    return result


def build(data_dir: Path, schema_path: Path, output_path: Path) -> BuildResult:
    output_path = Path(output_path)
    result = assemble_artifact(data_dir, schema_path)
    result.output_path = output_path
    if not result.success:
        return result

    write_bytes_atomically(output_path, serialize_json_deterministic(result.artifact))
    result.wrote_output = True
    return result
