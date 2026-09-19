# Architecture (Conceptual — Phase 00 / Builder MVP — Phase 01.0)

**Status.** As of Phase 01.0, a minimal Builder (`tools/builder/`) exists
and implements a small slice of the pipeline below against
`data/curated/*.json` only — see `docs/04_BUILDER.md` for exactly what it
does. No SQLite pack, no manifest, no updater, and no CI exist yet, and no
external source has been ingested. Nothing in this document beyond what
`docs/04_BUILDER.md` describes runs automatically.

## Conceptual data pipeline

```text
Sources
  ↓
normalize                        \
  ↓                                }  implemented by the Phase 01.0
deduplicate                       /   Builder MVP, scoped to
  ↓                              /    data/curated/*.json only --
canonicalization                /     see docs/04_BUILDER.md
  ↓                             /
alias generation/import        /
  ↓                            |
collision detection            |  implemented (comparison/collision
  ↓                            |  analysis only, not a full pipeline
ambiguity classification       /  stage in its own right yet)
  ↓
source/license validation        <- not implemented (no external
  ↓                                  sources exist to validate)
schema validation                 <- implemented (JSON Schema stage)
  ↓
distribution package               <- not implemented (dist/gvp.json is
                                       an intermediate MVP artifact, not
                                       a distribution package/manifest)
```

Phase 00.2 defined the contract the *end* of this pipeline must produce
(`schema/gvp.schema.json`) and the policies (`docs/03_COLLISION_POLICY.md`).
Phase 01.0 implements loading, schema validation, semantic validation,
comparison-only normalization, and collision analysis against the existing
curated fixture set, and writes a deterministic `dist/gvp.json`. It does
**not** implement source ingestion, deduplication across multiple raw
sources, license validation, or any distribution/release packaging — those
remain future work.

## Versioning model

EXPC-GVP has three independent version axes. They must never be conflated:

| Axis | What it versions | Scheme | Where recorded |
|---|---|---|---|
| **Schema version** | The *contract* (`schema/gvp.schema.json`) | SemVer-like, e.g. `0.1.0` | `x-schema-version` field inside the schema file itself |
| **Builder version** | The tool that produces build artifacts | SemVer | `__builder_version__` in `tools/builder/__init__.py`. Phase 01.0 MVP starts at `0.1.0-mvp`; not yet published via any manifest/package metadata. |
| **Data Pack version** | A released, versioned bundle of vocabulary data | CalVer (date-based) | A future `manifest.json`, once releases exist |

A new Data Pack release does **not** imply a new schema version — most
releases will just add/update entities under the existing schema. A schema
version only changes when the *shape of an entity document itself* changes
in a way old consumers need to know about. See `docs/01_DATA_SCHEMA.md` for
schema version details and compatibility rules.

## Privacy boundary / intake classification

The public EXPC-GVP repository never automatically accepts:

- raw user dictation
- personal names
- client names
- private phrases
- internal organization vocabulary

Any future intake process (manual or tooled) must first classify candidate
data as one of:

- **Personal** — scoped to an individual/private context
- **Organization** — scoped to a specific organization, not universally public
- **Global candidate** — potentially suitable for the public pack

Only entries classified as **Global candidate**, and then reviewed against
`SOURCES.md` and `CONTRIBUTING.md`, may be added to this public repository's
`data/`. See `docs/02_VOCABULARY_LAYERS.md` for the full layer model and
`SECURITY.md` for the hard privacy rules.

## Related documents

- `docs/01_DATA_SCHEMA.md` — the entity schema, field by field
- `docs/02_VOCABULARY_LAYERS.md` — Global / Domain / Organization / Personal
- `docs/03_COLLISION_POLICY.md` — ambiguity levels and collision handling
- `docs/04_BUILDER.md` — the Phase 01.0 Builder MVP: command, stages, output, limitations
