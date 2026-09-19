"""
EXPC-GVP Builder (Phase 01.0 MVP).

Validates data/curated/*.json against schema/gvp.schema.json, runs
cross-record semantic checks and collision analysis, and writes a
deterministic dist/gvp.json artifact. See docs/00_ARCHITECTURE.md for
where this fits in the (still mostly conceptual) pipeline, and
docs/01_DATA_SCHEMA.md for why Builder SemVer is a version axis
independent of the schema version and the future Data Pack CalVer.

Phase 01.0 scope only: no SQLite, no manifest, no updater, no CI.
"""

__builder_version__ = "0.2.0-mvp"
# 0.2.0-mvp (Phase 01.1): Builder now resolves per-alias effective policy
# (tools/builder/policy.py) and reasons about collisions at alias
# granularity instead of whole-entity granularity. Backward-compatible
# with all Phase 01.0 fixture data (legacy plain-string aliases still
# work unchanged) -- a MINOR bump, not a MAJOR one, mirroring the schema
# version bump from 0.1.0 to 0.2.0 for the same reason. See
# docs/01_DATA_SCHEMA.md "Per-alias policy model".
