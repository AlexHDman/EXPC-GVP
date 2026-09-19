# Builder (Phase 01.0 MVP)

**Status: minimal, working, and narrow in scope.** `tools/builder/` exists
and produces a real, deterministic artifact from the curated fixture data.
It is not a general-purpose data pipeline yet — see "Explicitly out of
scope" below before assuming it does more than it does.

## Command

Run from the repository root:

```
py -3.12 -m tools.builder build
```

Optional flags (all default to the real repository paths):

```
py -3.12 -m tools.builder build --data-dir data/curated --schema schema/gvp.schema.json --output dist/gvp.json
```

Exit code `0` on success, non-zero on any failure. On failure, no output
file is written or modified (see "Safe write" below).

## Input

`data/curated/*.json` — every file matching that glob is treated as one
vocabulary entity. There is currently no support for entities split across
`data/brands/`, `data/software/`, etc. (those directories remain empty
placeholders; see `docs/02_VOCABULARY_LAYERS.md` / repository taxonomy).

## Pipeline stages

1. **Load** (`tools/builder/loader.py`) — read every `data/curated/*.json`
   file. No validation happens at this stage.
2. **JSON Schema validation** (`tools/builder/validator.py`,
   `validate_schema_conformance`) — every entity must validate against
   `schema/gvp.schema.json`. This is the *structural* contract: required
   keys, types, enums, and the schema's own cross-field constraints
   (`ambiguity: high` / `policy: context_required` ⇒ `auto_replace: false`).
   Any failure here stops the build before later stages run.
3. **Semantic validation** (`validator.py`, `validate_semantics`) —
   cross-record and normalization-aware checks that JSON Schema cannot
   express on its own:
   - unique `id` across all entities;
   - `canonical` non-empty *after* normalization (catches whitespace-only
     values the schema's `minLength: 1` would let through);
   - no two entities normalize to the same `canonical`;
   - no duplicate aliases within one entity after normalization (catches
     case/whitespace variants the schema's `uniqueItems` would miss);
   - `layer` is `global` or `domain` only (this public repository's own
     rule — the schema itself permits `organization`/`personal` because
     it is reusable by private stores, see `docs/02_VOCABULARY_LAYERS.md`);
   - no out-of-scope organization terms (EXPC/FOHOW/RUS177) anywhere in
     the entity.

   Deliberately **not** re-checked here: required keys, enum membership,
   and the ambiguity/policy → `auto_replace` constraint — the schema
   already enforces those exactly, and re-deriving them in Python would
   just be the schema duplicated by hand.
4. **Normalization for comparison** (`tools/builder/normalize.py`) — used
   internally by stages 3 and 5 only: Unicode NFC, trim, collapse internal
   whitespace, casefold. **Never** applied to what gets written to the
   output artifact — `canonical` in `dist/gvp.json` is always the verbatim
   curator-approved string (`NVIDIA` stays `NVIDIA`).
5. **Collision analysis** (`tools/builder/collisions.py`) — implements
   `docs/03_COLLISION_POLICY.md` as code. Produces two buckets:
   - **blocking** — a normalized alias is shared by two or more entities
     *and* at least one of them claims `auto_replace: true` for it. That
     is a contradiction in the data (it can't be safe to blindly replace a
     string that doesn't uniquely identify one entity) and fails the
     build.
   - **contextual** — a known, already-flagged ambiguity that does *not*
     fail the build: entities with `ambiguity` in `medium`/`high`,
     `policy: context_required`, `auto_replace: false`, or a legitimately
     shared alias where every owner already agrees not to auto-replace.
     `software.cuda` (`куда`) is the canonical example — `ambiguity: high`
     keeps it out of the blocking bucket while still surfacing it in the
     summary.

   This stage only *analyzes* the dataset. It does not implement alias
   matching/replacement against arbitrary text — that is future consumer
   responsibility, not the Builder's.
6. **Deterministic build artifact** (`tools/builder/build.py`) — only
   reached if every earlier stage passed with zero blocking collisions.

## Output: `dist/gvp.json`

An intermediate MVP artifact, not the final distribution format:

```json
{
  "schema_version": "0.1.0",
  "entity_count": 15,
  "entities": [ /* full entity objects, sorted by id ascending */ ]
}
```

Properties:
- UTF-8, `ensure_ascii=False` (Cyrillic stays literal Cyrillic, not
  `\uXXXX` escapes), 2-space indent, trailing newline, `\n` line endings.
- `entities` is sorted by `id` — deterministic regardless of filesystem
  directory-listing order.
- No timestamp, no build-machine metadata, no random ordering: identical
  input always produces byte-identical output.
- Contains only entity data plus the schema version it validated against
  — no manifest fields (hashes, release metadata, etc.) yet.

## Safe / atomic write

`dist/gvp.json` is never written to directly. The Builder writes to a temp
file in the same directory (so the following replace is atomic on the same
filesystem), then `os.replace()`s it into place — only after every
validation/collision stage has already passed in memory. On any failure,
no temp file is left behind and any previously-existing valid
`dist/gvp.json` is untouched.

## CLI summary output

```text
EXPC-GVP Builder
Schema: 0.1.0
Entities: 15
Schema validation: PASS
Semantic validation: PASS
Collisions: 0 blocking / 5 contextual
Output: dist/gvp.json
BUILD: PASS
```

On failure, the summary stops at the first failing stage and prints
`BUILD: FAIL`; the process exits non-zero.

## Explicitly out of scope (Phase 01.0)

Not implemented by this Builder, and not to be assumed working:

- SQLite (or any other compiled) data pack
- a release manifest, SHA-256 checksums, or any updater
- GitHub Actions / CI wiring (the Builder must currently be run manually)
- GitHub Releases or tags
- Wikidata import or any other external source adapter
- ingestion from anything other than `data/curated/*.json`
- deduplication/canonicalization across multiple raw sources (there is
  only one curated source right now)
- source/license validation (no external sources exist to validate)
- a consumer-facing alias replacement/matching engine
- fuzzy, phonetic, or NLP-based matching of any kind

## Tests

`tests/test_builder.py` covers: a successful build against the real
fixture data, byte-identical determinism across repeated builds, canonical
spelling preservation, stable `id` ordering, `software.cuda` staying
contextual/non-blocking, schema-failure and semantic-failure paths
(duplicate id, duplicate canonical after normalization, Unicode NFC vs NFD
duplicate detection), blocking vs. contextual collision handling, that a
failed build never overwrites a previously valid artifact, and both CLI
exit codes. Run with:

```
py -3.12 -m pytest tests/
```
