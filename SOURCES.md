# Source Policy Foundation

**Status: policy foundation only. No data has been imported.**

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

No sources have completed this review. No data has been formally imported
under this policy.

`data/curated/` does contain a small fixture/test dataset added in
Phase 00.2 to validate `schema/gvp.schema.json` itself (entity model,
collision policy, test suite). Every fixture entity is marked
`provenance.source: "curated"` (curator-authored from general knowledge) or
`"unverified"` — never `"official"` — and has not been run through this
source review process. It must not be treated as reviewed/authoritative
data. `data/brands/`, `data/software/`, `data/ai/`, `data/hardware/`,
`data/standards/`, and `data/networking/` remain empty placeholders.
