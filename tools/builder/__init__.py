"""
EXPC-GVP Builder (Phase 01.0 MVP).

Validates data/curated/*.json against schema/gvp.schema.json, runs
cross-record semantic checks and collision analysis, and writes a
deterministic dist/gvp.json artifact. Since Phase 02.0 it can also
package that same artifact into a versioned Data Pack (manifest.json +
checksums.sha256) and verify one. See docs/00_ARCHITECTURE.md for where
this fits in the (still mostly conceptual) pipeline, and
docs/01_DATA_SCHEMA.md for why Builder SemVer is a version axis
independent of the schema version and the Data Pack CalVer
(docs/05_DISTRIBUTION.md).

Phase 02.0 scope only: no SQLite, no compression, no updater, no CI, no
GitHub Release/tag, no network access.
"""

__builder_version__ = "0.2.1-mvp"
# 0.1.0-mvp (Phase 01.0): initial load/validate/collision-analyze/write
# pipeline against data/curated/*.json.
#
# 0.2.0-mvp (Phase 01.1): Builder now resolves per-alias effective policy
# (tools/builder/policy.py) and reasons about collisions at alias
# granularity instead of whole-entity granularity. Backward-compatible
# with all Phase 01.0 fixture data (legacy plain-string aliases still
# work unchanged) -- a MINOR bump, not a MAJOR one, mirroring the schema
# version bump from 0.1.0 to 0.2.0 for the same reason. See
# docs/01_DATA_SCHEMA.md "Per-alias policy model".
#
# 0.2.1-mvp (Phase 02.0): adds `package` (versioned Data Pack: gvp.json +
# manifest.json + checksums.sha256 under dist/<CalVer>/, staged and
# published atomically) and `verify` (standalone package integrity
# check), on top of the existing `build` command. A PATCH bump, not
# MINOR: it is new distribution *tooling* around the existing artifact,
# not a change to what the Builder validates or produces -- `build`'s
# own behavior, the entity schema it validates against
# (schema/gvp.schema.json stays at 0.2.0), and the existing CLI contract
# are all unchanged. This deliberately keeps Builder in the same 0.2.x
# line as the schema rather than opening a 0.3.x line, since the
# Phase 01.1 precedent ties a Builder MINOR bump to a schema MINOR bump
# (both moved together, 0.1.0 -> 0.2.0) -- Phase 02.0 doesn't touch the
# schema, so it doesn't earn a new Builder MINOR either. See
# docs/05_DISTRIBUTION.md.
