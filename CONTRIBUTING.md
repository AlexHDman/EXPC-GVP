# Contributing to EXPC-GVP

EXPC-GVP is in **Production / Maintenance Mode** (see
`docs/07_MAINTENANCE.md` for the full candidate-review flow this document
summarizes). You can propose:

- a new global term (brand, product, standard, protocol, etc.);
- a canonical spelling correction;
- a spoken/informal alias;
- an ambiguity/collision-safety correction (e.g. an alias that's riskier
  or safer than currently classified);
- a provenance correction (a wrong or missing source attribution).

**Do not submit personal, private, or client-specific vocabulary to the
public GVP** — see `SECURITY.md`. Only `global`/`domain`-layer, publicly
appropriate vocabulary belongs here (`docs/02_VOCABULARY_LAYERS.md`).

## Data contributions

- Every proposed data entry must state its **source and provenance** (see
  `SOURCES.md`). Entries without traceable provenance will not be accepted.
- Contributors must be aware of **collision and ambiguity**: a proposed
  alias or name may already map to a different canonical entity. Flag
  potential ambiguity explicitly in the contribution rather than silently
  resolving it.
- **No personal or private data.** Do not contribute personal names, private
  organizational data, client information, or anything scoped to an
  individual/private context (see `SECURITY.md`).
- **Schema validation.** `schema/gvp.schema.json` exists and
  `tests/test_schema.py` validates every file under `data/curated/` against
  it. As of Phase 01.0, `py -3.12 -m tools.builder build` also validates the
  same data (schema + semantic + collision checks) and will refuse to
  produce `dist/gvp.json` if anything fails — see `docs/04_BUILDER.md`. Any
  new data contribution must validate against both. Neither is wired into
  any automated CI check yet — running `pytest` / the Builder locally is
  currently a manual step — and neither replaces the source/provenance
  review against this document and `SOURCES.md`.
- Ordinary data additions are expected, in the future, to go through a
  **data pull request** scoped only to `data/` content.

## Architecture, schema, and builder changes

- Changes to repository architecture, the schema (`schema/`), or the
  builder/tooling (`tools/`) are **not** ordinary data contributions and
  require a separate, dedicated review — they affect every consumer of the
  vocabulary pack.

## Current status

EXPC-GVP has published its first production Data Pack (437 entities,
schema `0.2.0`). A local test suite (`tests/`, run via `pytest`) covers
schema validation, automated collision detection, and the Builder
(`tools/builder/`, see `docs/04_BUILDER.md`, `docs/05_DISTRIBUTION.md`,
`docs/06_RELEASE_CONTRACT.md`). Automated CI (GitHub Actions or similar)
does not exist yet — nothing runs these checks automatically on push/PR;
`pytest` and the Builder must be run manually before any change is
proposed.
