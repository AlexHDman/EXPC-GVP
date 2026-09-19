# Collision & Ambiguity Policy

This document defines how EXPC-GVP classifies ambiguity, and what behavior
each classification implies for a consumer deciding whether to
auto-replace an alias with its canonical form. It is policy/documentation;
the machine-enforced parts of it live in `schema/gvp.schema.json` (see
"Cross-field constraints" in `docs/01_DATA_SCHEMA.md`).

**Since Phase 01.1 (schema 0.2.0), ambiguity/policy/auto_replace are
resolved per *alias*, not just per entity** — see
`docs/01_DATA_SCHEMA.md` → "Per-alias policy model" for the mechanism
(entity defaults → optional alias overrides → effective policy). The
levels and examples below describe the same classification, now applied
per-alias; entity-level values remain the default/fallback for any alias
that does not specify its own override.

## Ambiguity levels

### `low`

The alias is specific enough that it is unlikely to collide with ordinary
language or with a different canonical entity. `auto_replace: true` is
permitted, but not required — a low-ambiguity entity may still set
`auto_replace: false` if a curator is not yet confident.

Example from the Phase 00.2 fixture: `NVIDIA` — alias `нвидиа` is not a
common Russian word and is not shared with any other fixture entity.

### `medium`

The alias carries a real but bounded collision risk — e.g. it overlaps with
a common word, a common personal name, or another term, but usually only in
specific contexts. Additional checks (context/domain hints, word-boundary
checks) are required before replacing. By default, `auto_replace` should be
`false` for `medium` until a consumer implements those checks.

Examples from the fixture:

- `Docker` — alias `докер` collides with the ordinary Russian word "докер"
  (dockworker/stevedore).
- `Claude` — alias `клод` collides with the common transliteration of the
  French given name "Claude" (e.g. Claude Monet → "Клод Моне").
- `Wi-Fi` — alias `вафля` (Russian internet slang for Wi-Fi) collides with
  the ordinary word "вафля" (waffle). Since Phase 01.1 this is a
  **per-alias override** on `standard.wifi`, not the entity default — see
  "Wi-Fi worked example" below.
- `Xray` (the software) — alias `иксрей`/`икс-рей` collides with the
  common Russian rendering of "x-ray" in its medical-imaging sense
  ("рентген" is more common, but "икс-рей" is also used colloquially).

### `high`

The alias is a common word, a high-frequency function word, or otherwise so
likely to appear in unrelated speech/text that blind replacement would
produce frequent false positives. **Default: `policy = context_required`
and `auto_replace = false`.** The schema enforces this: an entity with
`ambiguity: "high"` cannot validly have `auto_replace: true`.

Canonical example: `CUDA` — alias `куда` is the common Russian
interrogative/adverb "куда" ("where to"). It must never be replaced with
`CUDA` without strong IT/GPU-context signals.

## Mechanics consumers must apply (once a consumer/builder exists)

- **Exact token boundaries.** Match aliases on word boundaries, not
  arbitrary substrings, so that e.g. `куда` inside a longer unrelated word
  is not falsely matched.
- **Case handling.** Matching should be case-insensitive for Latin-script
  canonical/alias forms unless a specific entity's collision profile
  requires case-sensitivity; case must never be used as the *only* signal
  distinguishing two different canonical entities.
- **Unicode normalization.** All strings should be compared in Unicode NFC
  form, so that visually identical strings encoded differently do not
  silently fail to match or silently create duplicate entries. Fixture data
  in this repository is authored in NFC and tested for it
  (`tests/test_schema.py`).
- **Overlapping aliases.** The same alias string may legitimately be
  claimed by more than one canonical entity across the whole vocabulary
  (this is what "collision" means here). Detecting this — an alias
  string that maps to two or more different `id`s — is a required check
  before publishing any data pack; see the collision-detection test in
  `tests/test_schema.py` for a minimal implementation.
- **Alias → multiple canonical entities.** When an alias is genuinely
  shared, no automatic tie-break is safe by default; treat it the same as
  `high` ambiguity for that alias until a domain/context hint resolves it.
- **Common-language collisions.** Treat collision with an ordinary
  dictionary word or common name as at least `medium`, per the examples
  above.
- **Domain/context hints.** A future consumer may use surrounding text
  (e.g. presence of other IT/GPU terms near `куда`) to raise confidence
  above the default; this repository does not implement such logic, it only
  records the ambiguity classification that such logic would need to
  consult.
- **Deterministic conflict resolution.** Given the same input and the same
  data pack version, collision/ambiguity handling must always produce the
  same decision — no randomness, no non-deterministic tie-breaking.
- **Fail-safe principle.** When confidence is insufficient, **do not
  replace**. Silence (leaving the original text untouched) is always the
  safe default outcome; a wrong automatic replacement is worse than no
  replacement.

## Wi-Fi worked example (per-alias policy, Phase 01.1)

`standard.wifi`'s entity-level defaults are now the safe/common case:
`ambiguity: low`, `policy: canonical_preferred`, `auto_replace: true`.

```text
Wi-Fi
├── вайфай  (plain string alias, inherits entity defaults)
│     → effective: low / canonical_preferred / auto_replace=true
└── вафля   (structured alias, overrides all three fields)
      → effective: medium / canonical_preferred / auto_replace=false
```

`вайфай` is an ordinary informal spelling with no real collision risk, so
it is left as a plain legacy string and simply inherits the entity's safe
defaults. `вафля` is genuinely risky (it collides with the everyday word
"waffle"), so it is a structured alias overriding `ambiguity`, `policy`,
and `auto_replace` to the more conservative values on itself — without
having to make the *whole entity* conservative and understate how safe
`вайфай` actually is.

## CUDA worked example (pure inheritance, no override needed)

`software.cuda`'s single alias `куда` is left as a plain legacy string —
no structured override was added, because none was needed: the entity's
own `ambiguity: high` / `policy: context_required` / `auto_replace: false`
already produce the correct effective policy for its only alias. This is
deliberate: not every entity needs migrating to the structured form, only
ones whose aliases actually have differing risk profiles (see
`docs/01_DATA_SCHEMA.md` → "Per-alias policy model").

## Changelog

- **Phase 01.1 (schema 0.2.0).** Resolved the per-entity-only limitation
  flagged in Phase 00.2 (quoted below for the historical record). Aliases
  may now individually override `ambiguity`/`policy`/`auto_replace`; see
  `docs/01_DATA_SCHEMA.md` → "Per-alias policy model" for the inheritance
  rule and safety invariant, and the two worked examples above.

  > Original Phase 00.2 note: "Ambiguity is currently modeled **per
  > entity**, not per individual alias. `Wi-Fi` has both a very safe alias
  > (`вайфай`) and a much riskier one (`вафля`) under a single
  > `ambiguity: "medium"` value for the whole entity. This is a known
  > simplification."
