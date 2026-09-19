# Vocabulary Layers

EXPC-GVP's vocabulary model is organized into four layers. This document
defines them precisely and states, unambiguously, which layers this public
repository may contain.

## The four layers

1. **Global** — universally applicable entries, meaningful regardless of any
   specific organization or individual. Example: `Microsoft`, `NVMe`.
2. **Domain** — entries specific to a subject-matter domain (e.g. IT/AI),
   still public, but narrower than "universally applicable". Example: a
   term specific to a niche technical field that is public knowledge but
   not broadly recognized outside that field.
3. **Organization** — entries scoped to a particular organization. Example:
   `EXPC`, `FOHOW`, `RUS177`.
4. **Personal** — entries scoped to an individual user or context. Example:
   surnames, client names, or any other individually-scoped term.

## Worked examples (from the project brief)

| Term | Layer |
|---|---|
| Microsoft | Global |
| NVMe | Global / IT |
| CUDA | Global / AI-IT |
| EXPC | Organization |
| FOHOW | Organization |
| RUS177 | Organization |
| Surnames / client names | Personal |

## `kind` vs `layer` — two different axes

Do not confuse a vocabulary entity's **`kind`** (what *type* of thing it is
— a brand, a piece of software, a standard, etc.) with its **`layer`** (how
*broadly public/scoped* it is). A company name like `OpenAI` is `kind:
"brand"` **and** `layer: "global"` at the same time — being a "brand" says
nothing about whether it belongs in the public pack; being publicly and
universally known is what makes it `global`.

## Public repository boundary

**This public EXPC-GVP repository's `data/` directory must only ever
contain entries with `layer: "global"` or `layer: "domain"`.**

`layer: "organization"` and `layer: "personal"` are valid values in
`schema/gvp.schema.json` because the same schema is designed to be reusable
by private, non-public vocabulary stores (e.g. an organization's own
internal vocabulary layered on top of the public Global layer). They must
**never** be used for real entries committed to this public repository. The
fixture dataset added in Phase 00.2 (`data/curated/`) intentionally contains
only `layer: "global"` entries and no Organization/Personal examples, even
though such examples exist conceptually (see the table above).

See `docs/00_ARCHITECTURE.md` → "Privacy boundary / intake classification"
and `SECURITY.md` for the enforcement-side rules.
