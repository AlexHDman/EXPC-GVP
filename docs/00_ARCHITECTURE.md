# Architecture (Conceptual — Phase 00)

**Status: this document describes an intended pipeline, not an implemented
one.** As of Phase 00.2, no builder, no SQLite pack, no manifest, and no
updater exist. Nothing described here runs automatically.

## Conceptual data pipeline

```text
Sources
  ↓
normalize
  ↓
deduplicate
  ↓
canonicalization
  ↓
alias generation/import
  ↓
collision detection
  ↓
ambiguity classification
  ↓
source/license validation
  ↓
schema validation
  ↓
distribution package
```

Each stage above is a future responsibility of a Builder that does not exist
yet. Phase 00.2 only defines the contract the *end* of this pipeline must
produce (`schema/gvp.schema.json`) and the policies (`docs/03_COLLISION_POLICY.md`)
that stages such as "collision detection" and "ambiguity classification" will
eventually implement. It does not implement any stage.

## Versioning model

EXPC-GVP has three independent version axes. They must never be conflated:

| Axis | What it versions | Scheme | Where recorded |
|---|---|---|---|
| **Schema version** | The *contract* (`schema/gvp.schema.json`) | SemVer-like, e.g. `0.1.0` | `x-schema-version` field inside the schema file itself |
| **Builder version** | The (future) tool that produces data packs | SemVer | Builder's own manifest/package metadata, once it exists |
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
