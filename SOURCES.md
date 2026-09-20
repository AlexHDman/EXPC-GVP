# Source Policy Foundation

**Status: policy foundation, plus a per-entity provenance audit (Phase
03).** No *external dataset* has been bulk-imported (no Wikidata scrape,
no third-party database) — see "Current state" below for exactly what
has and has not happened.

This document defines the categories of sources EXPC-GVP may eventually draw
from and the review requirements each source must pass before any data from
it is imported. It does not itself authorize or perform any import.

## Potential future source categories

- Official vendor sources
- IANA
- Wikidata
- AI / model catalogs
- Curated EXPC sources (internally produced)
- Other sources — only after a license/provenance review, added to this
  list on a case-by-case basis

## Required review fields per source

Before any source is used to populate `data/`, the following must be
recorded for it, here or in a linked per-source document:

| Field | Description |
|---|---|
| Source identity | Name/owner of the source |
| Source URL / source ID | Where the source is published or referenced |
| License / terms | The license or terms of use governing the source |
| Redistribution permission | Whether redistribution (as part of a compiled EXPC-GVP package) is permitted, and under what conditions |
| Provenance | How the data was obtained and by whom |
| Last verified date | When the above was last checked/confirmed |
| Confidence | Confidence level in the accuracy/currency of the above |

## Current state

No *source* (in the sense of an external dataset/catalog this project
would bulk-import from, per the table above) has completed the full
review this document describes, and no such external dataset has been
imported. `data/brands/`, `data/software/`, `data/ai/`, `data/hardware/`,
`data/standards/`, and `data/networking/` remain empty placeholders.

`data/curated/` contains this project's own production dataset (437
entities as of the `2026.09.20.2` Data Pack), curator-authored from
general/public knowledge, not sourced from a bulk external dataset.
Phase 03 added a **per-entity** provenance pass distinct from the
source-level review above: for an entity representing a product, brand,
or standard with one confidently-known, identifiable owning organization
or standards body, `provenance.source` is `"official"` and
`provenance.source_url` names that organization's or body's own
reference domain (e.g. `usb.org` for USB, `python.org` for Python,
`ietf.org` for TCP/DNS/HTTP). This reflects strong confidence in the
entity's identity and canonical spelling — **it is not a claim that this
document's formal per-source review (redistribution permission, license
terms, a dated verification) has been completed for that
organization/body**; `provenance.license` and `provenance.last_verified`
are `null` throughout, honestly, for exactly that reason. Where no single
owning authority could be confidently identified, `provenance.source`
remains `"curated"` (124 of 437 entities) rather than guessing. As of `2026.09.20.2`, every entity uses either
`"official"` (313) or `"curated"` (124) — none uses `"community"` or
`"unverified"`.
