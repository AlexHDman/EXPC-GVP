# Data Schema

Schema file: `schema/gvp.schema.json`
Schema draft: JSON Schema 2020-12
Schema version: `0.1.0` (see the `x-schema-version` field inside the schema
file; this is EXPC-GVP-specific metadata, not a JSON Schema keyword)

This document explains every field of a vocabulary entity: whether it is
required, what values it accepts, and what it is for. It is a companion to
the machine-readable schema, not a replacement for it — the schema file is
authoritative for validation.

## Field reference

| Field | Required | Type | Notes |
|---|---|---|---|
| `id` | yes | string | Stable identifier, convention `<kind>.<slug>` (e.g. `brand.microsoft`). Never reused once published. |
| `kind` | yes | string enum | `brand`, `software`, `ai_model`, `hardware`, `standard`, `networking`. Closed set aligned with the `data/` subdirectory taxonomy. |
| `layer` | yes | string enum | `global`, `domain`, `organization`, `personal`. See `docs/02_VOCABULARY_LAYERS.md`. This public repository only ever contains `global`/`domain` entries. |
| `language` | yes | string | ISO 639-1 code of the `canonical` spelling itself (e.g. `en`), not the entity's country of origin. |
| `canonical` | yes | string, non-empty | The canonical original spelling. Default principle: *prefer canonical original*. |
| `aliases` | yes | object | Map of language code → array of alternate spoken/written forms. May be `{}` if none are known yet. |
| `ru_equivalent` | yes (nullable) | string or null | A genuine Russian **translation/semantic equivalent**, if one exists. |
| `ru_transcription` | yes (nullable) | string or null | The preferred Russian **phonetic transcription** of `canonical`. |
| `policy` | yes | string enum | `canonical_preferred`, `context_required`. See collision policy doc. |
| `ambiguity` | yes | string enum | `low`, `medium`, `high`. See collision policy doc. |
| `auto_replace` | yes | boolean | Whether a consumer may blindly auto-replace an alias with `canonical`. Constrained by `ambiguity`/`policy` (see below). |
| `provenance` | yes | object | See sub-table below. |

### `provenance` sub-fields

| Field | Required | Type | Notes |
|---|---|---|---|
| `source` | yes | string enum | `official`, `curated`, `community`, `unverified`. |
| `source_url` | yes (nullable) | string or null | Loosely pattern-checked (`^https?://`), not strictly URI-validated (no extra dependency at this phase). |
| `source_id` | yes (nullable) | string or null | |
| `license` | yes (nullable) | string or null | |
| `confidence` | yes | number 0-1 | Curator confidence. Not a substitute for `source`. |
| `last_verified` | yes (nullable) | string or null | `YYYY-MM-DD`, or null if never formally verified against `SOURCES.md`. |

Every `provenance` sub-field is **required as a key**, even when its value is
`null`. This is deliberate: an entry must explicitly state "unverified/null"
rather than silently omitting a field, so that "we don't know yet" is always
distinguishable from "this field doesn't exist in this schema version".

## `canonical` vs `ru_equivalent` vs `ru_transcription` vs `aliases`

These four fields are easy to conflate. They answer four different
questions and must never be merged into one:

- **`canonical`** — "What is the correct original name/spelling of this
  entity?" Example: `Microsoft`, `CUDA`, `Wi-Fi`.
- **`ru_equivalent`** — "Is there an actual Russian word that *means* the
  same thing, as a translation?" Most proper nouns/brand names have none, so
  `null` is the normal, expected value. Illustrative (non-fixture) example:
  canonical `mouse` (the computer peripheral) → `ru_equivalent: "мышь"`
  (the real Russian word for it).
- **`ru_transcription`** — "How would a Russian speaker phonetically write
  this term in Cyrillic, as the *preferred* rendering?" Same `mouse`
  example → `ru_transcription: "маус"` (a phonetic loan rendering, distinct
  from the semantic translation `мышь`).
- **`aliases.ru`** — "What other forms do people actually say/write?" This
  can include informal slang, abbreviations, and even the transcription
  itself as one of several variants (e.g. Windows → `aliases.ru: ["винда",
  "виндовс"]`), but it is not a single canonical/preferred value — it is a
  list of *observed* alternate forms, some of which may carry collision risk
  (see `docs/03_COLLISION_POLICY.md`).

None of these fields is a fallback for another. A `null` `ru_equivalent`
does not mean "use `ru_transcription` instead" at the schema level — that
substitution, if any, is a consumer-side policy decision.

## `id` / `kind` convention

By convention, `id` is `<kind>.<slug>`. This schema does **not** enforce that
the `id` prefix matches `kind` via a JSON Schema `pattern`/`if`/`then`,
because a single regex per `kind` value would need to be duplicated and
kept in sync with the `kind` enum, which is a maintenance hazard for little
benefit. Instead, `tests/test_schema.py` enforces this convention directly
against the fixture data. Future data outside this repository's own tests
should apply the same check in its own validation step.

## Cross-field constraints (enforced by the schema itself)

The schema enforces, via `allOf`/`if`/`then`:

- `ambiguity == "high"` ⇒ `auto_replace` must be `false`.
- `policy == "context_required"` ⇒ `auto_replace` must be `false`.

These are schema-level, machine-checked invariants — not just documentation.
An entity that violates either rule fails `jsonschema` validation.

## Forward compatibility

- The root entity object and the `provenance` object both use
  `"additionalProperties": true` deliberately, so that a future minor schema
  version can add optional fields without breaking documents/consumers built
  against schema `0.1.0`. `tests/test_schema.py` additionally enforces a
  stricter *known-keys* check against this repository's own current fixture
  data, so our own typos are still caught now.
- `aliases` uses `"additionalProperties": false` internally — only two-letter
  language-code keys are accepted there, since that structure is a closed
  dictionary shape, not a place where ad-hoc new top-level fields get added.
- The `policy` enum may gain values in a future minor schema version. Any
  consumer encountering an unrecognized `policy` value **must** fail safe
  and behave as if it were `context_required` (never assume it is safe to
  auto-replace an unrecognized policy).

## Schema version vs Builder SemVer vs Data Pack CalVer

See `docs/00_ARCHITECTURE.md` → "Versioning model" for the full three-axis
explanation. In short: bumping the schema version is rare and deliberate
(shape of an entity document changes); Builder SemVer and Data Pack CalVer
are unrelated axes that will be introduced when those components exist.
