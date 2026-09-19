# Data Schema

Schema file: `schema/gvp.schema.json`
Schema draft: JSON Schema 2020-12
Schema version: `0.2.0` (see the `x-schema-version` field inside the schema
file; this is EXPC-GVP-specific metadata, not a JSON Schema keyword).
`0.2.0` (Phase 01.1) added the structured/per-alias form described in
"Per-alias policy model" below; every `0.1.0` document remains valid
unchanged -- see that section for why this was a MINOR, not MAJOR, bump.

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
| `aliases` | yes | object | Map of language code → array of alternate spoken/written forms. May be `{}` if none are known yet. Each array item is either a plain string or a structured object with optional per-alias policy overrides -- see "Per-alias policy model" below. |
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

## Per-alias policy model (schema 0.2.0, Phase 01.1)

Through schema `0.1.0`, `ambiguity`/`policy`/`auto_replace` were only
knowable at the whole-entity level. That was a known simplification (see
`docs/03_COLLISION_POLICY.md`'s changelog note): a single entity can have
aliases with very different real-world collision risk. `Wi-Fi` is the
motivating fixture example — `вайфай` is an unremarkable spoken form with
essentially no collision risk, while `вафля` is Russian internet slang for
Wi-Fi that also happens to be the ordinary word for "waffle".

Since schema `0.2.0`, each item of `aliases['<lang>']` is one of two
shapes:

- **Plain string** (legacy/simple form, unchanged since `0.1.0`) — e.g.
  `"вайфай"`. Fully inherits `ambiguity`/`policy`/`auto_replace` from the
  entity; behaves exactly as it always has.
- **Structured object** — `{"value": "вафля", "ambiguity"?: ...,
  "policy"?: ..., "auto_replace"?: ...}`. `value` is required (the alias
  text itself, equivalent to what the plain-string form would be); the
  other three fields are each optional and, independently, override the
  entity's field of the same name for this alias only.

### Inheritance rule: entity defaults → alias overrides → effective policy

For each of `ambiguity`, `policy`, and `auto_replace`, independently:

> **effective alias value = the alias's own field, if present; otherwise
> the entity's field of the same name.**

This is *per-field* inheritance, not all-or-nothing — a structured alias
can override just `ambiguity` while still inheriting the entity's
`policy` and `auto_replace`. The result of merging all three fields this
way for one alias is that alias's **effective policy**
(`tools/builder/policy.py: resolve_effective_policy`).

### Worked examples

`software.cuda` — the single alias `куда` is left as a plain legacy
string; it has no overrides at all, so its effective policy is purely
the entity's own: `ambiguity=high`, `policy=context_required`,
`auto_replace=false`. Nothing needed to change here — this fixture is the
worked example proving legacy aliases keep working unchanged.

`standard.wifi` — the entity's own defaults were promoted to the safe,
common case (`ambiguity=low`, `policy=canonical_preferred`,
`auto_replace=true`), matching what most of its aliases actually are.
`вайфай` is left as a plain string, so it inherits that safe default.
`вафля` is a structured alias overriding all three fields to the riskier
values: `{"value": "вафля", "ambiguity": "medium", "policy":
"canonical_preferred", "auto_replace": false}`. Two aliases of the same
entity now correctly have two different effective policies.

### Safety invariant on the EFFECTIVE policy, not just the raw fields

The same invariant that applies at entity level applies to every alias's
*effective* policy, regardless of whether each field came from the alias
or was inherited from the entity:

- effective `ambiguity == "high"` ⇒ effective `auto_replace` must be `false`.
- effective `policy == "context_required"` ⇒ effective `auto_replace` must be `false`.

This is enforced in two layers, because no single layer can see enough
on its own:

1. **Schema (`$defs/alias_entry`)** — rejects a structured alias that is
   *locally* self-contradictory: if the alias object itself states
   `ambiguity: "high"` (or `policy: "context_required"`), that same
   object must also state `auto_replace: false`. The schema cannot see
   the entity's own fields from inside an alias object, so it cannot
   catch everything.
2. **Builder (`tools/builder/policy.py` +
   `tools/builder/validator.py`)** — resolves the effective policy by
   merging the alias with its entity, then checks the invariant against
   that merged result. This is what catches the case the schema
   structurally cannot: an alias that overrides *only* `auto_replace:
   true`, while `ambiguity`/`policy` are left to inherit an unsafe
   entity-level value. Neither layer's alias metadata is ever allowed to
   silently weaken the invariant — an unsafe combination is a build
   failure, not an auto-corrected value.

## Cross-field constraints (enforced by the schema itself)

The schema enforces, via `allOf`/`if`/`then`:

- `ambiguity == "high"` ⇒ `auto_replace` must be `false`.
- `policy == "context_required"` ⇒ `auto_replace` must be `false`.

These are schema-level, machine-checked invariants — not just documentation.
An entity that violates either rule fails `jsonschema` validation. The same
invariant is checked again at alias granularity — see "Per-alias policy
model" above.

## Forward compatibility

- The root entity object and the `provenance` object both use
  `"additionalProperties": true` deliberately, so that a future minor schema
  version can add optional fields without breaking documents/consumers built
  against an older schema version. `tests/test_schema.py` additionally
  enforces a stricter *known-keys* check against this repository's own
  current fixture data, so our own typos are still caught now.
- `aliases` uses `"additionalProperties": false` internally — only two-letter
  language-code keys are accepted there, since that structure is a closed
  dictionary shape, not a place where ad-hoc new top-level fields get added.
  The structured alias object form (`$defs/alias_entry`) similarly uses
  `"additionalProperties": false` — it is a small, closed shape (`value` +
  three optional overrides), not an open one for future alias-level
  metadata like per-alias provenance/confidence; extending it later is a
  deliberate future schema-version decision, not something silently
  possible today.
- The `policy` enum may gain values in a future minor schema version. Any
  consumer encountering an unrecognized `policy` value **must** fail safe
  and behave as if it were `context_required` (never assume it is safe to
  auto-replace an unrecognized policy).

## Schema version vs Builder SemVer vs Data Pack CalVer

See `docs/00_ARCHITECTURE.md` → "Versioning model" for the full three-axis
explanation. In short: bumping the schema version is rare and deliberate
(shape of an entity document changes); Builder SemVer and Data Pack CalVer
are unrelated axes that will be introduced when those components exist.

## Schema version history

| Version | Phase | Change |
|---|---|---|
| `0.1.0` | 00.2 | Initial entity contract. |
| `0.2.0` | 01.1 | Added the optional structured alias form (`$defs/alias_entry`) alongside the existing plain-string form, enabling per-alias `ambiguity`/`policy`/`auto_replace` overrides. Additive and backward-compatible: every `0.1.0` document is still valid under `0.2.0` unchanged — a MINOR bump, not MAJOR, per this document's own versioning model ("a schema version only changes when the shape of an entity document itself changes in a way old consumers need to know about" — old *consumers* reading `0.2.0` data they don't understand the new alias shape of would need to know about it, but no existing `0.1.0` *document* stops validating). |
