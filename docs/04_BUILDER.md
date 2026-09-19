# Builder (Phase 01.0 MVP, extended in Phase 01.1)

**Status: minimal, working, and narrow in scope.** `tools/builder/` exists
(`__builder_version__ = "0.2.0-mvp"`) and produces a real, deterministic
artifact from the curated fixture data. It is not a general-purpose data
pipeline yet — see "Explicitly out of scope" below before assuming it does
more than it does. Phase 01.1 added per-alias effective-policy resolution
(`tools/builder/policy.py`) and alias-granularity collision analysis; see
`docs/01_DATA_SCHEMA.md` → "Per-alias policy model" for the data model
this implements.

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
   - no duplicate aliases within one entity after normalization, across
     both the plain-string and structured representations (via
     `tools/builder/policy.py: alias_text`) — catches case/whitespace
     variants, and a legacy string vs. a structured object naming the
     same text, that the schema's `uniqueItems` would miss;
   - **(Phase 01.1) effective per-alias policy safety** — for every
     alias, resolves its *effective* `ambiguity`/`policy`/`auto_replace`
     (entity defaults merged with any alias override, see
     `tools/builder/policy.py`) and rejects the build if that effective
     combination violates the safety invariant (see below). This is the
     one check the schema structurally cannot perform itself, because it
     requires reaching across from an alias object to its entity's own
     fields;
   - `layer` is `global` or `domain` only (this public repository's own
     rule — the schema itself permits `organization`/`personal` because
     it is reusable by private stores, see `docs/02_VOCABULARY_LAYERS.md`);
   - no out-of-scope organization terms (EXPC/FOHOW/RUS177) anywhere in
     the entity.

   Deliberately **not** re-checked here: required keys, enum membership,
   the entity-level ambiguity/policy → `auto_replace` constraint, and a
   *locally* self-contradictory structured alias (one alias object that by
   itself states both `ambiguity: high` and `auto_replace: true`) — the
   schema already enforces those exactly, and re-deriving them in Python
   would just be the schema duplicated by hand.
4. **Normalization for comparison** (`tools/builder/normalize.py`) — used
   internally by stages 3 and 5 only: Unicode NFC, trim, collapse internal
   whitespace, casefold. **Never** applied to what gets written to the
   output artifact — `canonical` in `dist/gvp.json` is always the verbatim
   curator-approved string (`NVIDIA` stays `NVIDIA`), and a structured
   alias's `value` is preserved exactly as authored.
5. **Collision analysis** (`tools/builder/collisions.py`) — implements
   `docs/03_COLLISION_POLICY.md` as code, at **alias granularity** (Phase
   01.1; Phase 01.0 reasoned at whole-entity granularity). Every alias's
   *effective* policy (`tools/builder/policy.py`) is classified into one
   of two buckets:
   - **blocking** — a normalized alias value is shared by two or more
     entities *and* at least one owner's *effective* `auto_replace` is
     `true` for it. That is a contradiction in the data (it can't be safe
     to blindly replace a string that doesn't uniquely identify one
     entity) and fails the build.
   - **contextual** — a known, already-flagged, non-blocking ambiguity:
     any alias whose effective policy is not "freely safe to
     auto-replace" (`ambiguity` in `medium`/`high`, `policy:
     context_required`, or `auto_replace: false`), or a legitimately
     shared alias where every owner's effective `auto_replace` is already
     `false`. `software.cuda`'s `куда` is the canonical example (pure
     entity-level inheritance); `standard.wifi`'s `вафля` is the
     canonical per-alias-override example — its sibling alias `вайфай`
     does **not** appear here at all, since its effective policy is fully
     safe.

   Fail-safe principle: an alias is never assumed safe by default: it
   only counts as safe (absent from both buckets) once its effective
   policy is positively `low`/`canonical_preferred`/`auto_replace: true`.

   This stage only *analyzes* the dataset. It does not implement alias
   matching/replacement against arbitrary text, and no fuzzy/context/NLP
   classification is attempted — that remains future consumer
   responsibility, not the Builder's.
6. **Deterministic build artifact** (`tools/builder/build.py`) — only
   reached if every earlier stage passed with zero blocking collisions.

## Output: `dist/gvp.json`

An intermediate MVP artifact, not the final distribution format:

```json
{
  "schema_version": "0.2.0",
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
- Structured alias metadata is preserved exactly as authored — e.g.
  `standard.wifi`'s `aliases.ru` in the output is still
  `["вайфай", {"value": "вафля", "ambiguity": "medium", "policy":
  "canonical_preferred", "auto_replace": false}]`, not flattened or
  normalized into plain strings.

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
Schema: 0.2.0
Entities: 15
Schema validation: PASS
Semantic validation: PASS
Collisions: 0 blocking / 7 contextual
Output: dist/gvp.json
BUILD: PASS
```

The "7 contextual" count is at **alias** granularity (Phase 01.1), not
entity granularity — e.g. `standard.wifi` contributes exactly one entry
(`вафля`), not the whole entity, since its other alias (`вайфай`) is fully
safe. This is why the number differs from Phase 01.0's "5 contextual",
which counted flagged *entities*.

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
failed build never overwrites a previously valid artifact, both CLI exit
codes, and (Phase 01.1) legacy vs. structured alias validity, effective
per-alias policy inheritance and safety rejection, collision detection
using effective (not entity-default) policy, the Wi-Fi safe/risky worked
example, and structured alias metadata surviving into the output. Unit
tests for `tools/builder/policy.py` itself (effective-policy resolution in
isolation) live in `tests/test_policy.py`. Run with:

```
py -3.12 -m pytest tests/
```
