# Maintenance & Community Workflow (Production / Maintenance Mode)

**Status.** As of the `2026.09.20.2` Data Pack, EXPC-GVP has published its
first production release through the GitHub Release contract
(`docs/06_RELEASE_CONTRACT.md`) and enters **Production / Maintenance
Mode** — this is a state the project has entered, not a new numbered
development phase. This document is policy only — it does not implement
any automation. No candidate-intake tooling, scout system, or CI exists
yet.

## A. Production / Maintenance Mode

After a first release, EXPC-GVP is no longer in open-ended vocabulary
development. Changes are still expected, but they are **reactive and
reviewed**, not a continuous development sprint: each future Data Pack
version is a deliberate, reviewed release, not a rolling/nightly build.

## B. Where future vocabulary changes come from

Future changes may originate from:

- real-world consumer usage (a consuming application finding a canonical
  spelling, alias, or ambiguity classification that doesn't hold up);
- bug reports;
- GitHub Issues / Discussions / pull request feedback;
- new globally relevant technologies, standards, or products that did not
  exist or weren't yet significant at the time of a prior release;
- future candidate/scout tooling (**not implemented yet** — this document
  only reserves the idea; building such tooling is a separate, deliberate
  future decision, not something this document authorizes).

## C. What public GVP must never automatically ingest

Unchanged from `SECURITY.md`'s hard rule, restated here because it governs
every future *change*, not just the initial dataset:

- raw user dictation;
- personal names;
- customer/client information;
- private organization vocabulary;
- private phrases.

This applies regardless of source — a real-world usage report, an Issue,
or a PR can motivate a *general* correction (e.g. "this canonical spelling
is wrong", "this alias is ambiguous"), but the private data itself that
motivated the report must never be copied into the public dataset.

## D. Candidate flow

Every proposed vocabulary change — new entity, alias, canonical
correction, ambiguity/collision correction, or provenance correction —
goes through the same reviewed pipeline before it reaches a release:

```text
Candidate
  → classification            (Global vs. Domain vs. Organization/Personal —
                                 docs/02_VOCABULARY_LAYERS.md; only Global/Domain
                                 may ever enter this public repository)
  → provenance review          (SOURCES.md; prefer an authoritative
                                 first-party/standards-body source, per the
                                 Phase 03 provenance audit's approach)
  → alias/ambiguity review     (docs/03_COLLISION_POLICY.md; conservative
                                 by default -- see software.cuda's "куда")
  → collision analysis         (tools/builder/build.py; 0 blocking required)
  → schema/tests                (schema/gvp.schema.json; py -3.12 -m pytest tests/)
  → package verification       (package / verify / release-check --
                                 docs/05_DISTRIBUTION.md, docs/06_RELEASE_CONTRACT.md)
  → reviewed release            (a new, explicit Data Pack CalVer + tag +
                                 GitHub Release -- never silent/automatic)
```

Any step failing sends the candidate back, not forward.

## E. Role of AI / automation

AI tooling (including Claude Code / Codex-style assistants) may assist
with research, classification, provenance drafting, ambiguity/collision
audits, writing tests, and implementation work throughout the flow above.

**It must never autonomously publish unreviewed vocabulary into the
production data pack.** Every step in section D — especially provenance
review, ambiguity review, and the final release decision — requires
human review before it lands in a released Data Pack. AI assistance
speeds up preparing a candidate; it does not replace the review gate.

## F. Community feedback cadence

Issues, Discussions, and PR feedback should be reviewed periodically (no
fixed SLA is committed to here) and converted into **explicit, reviewed
development tasks** — not merged or acted on ad hoc. A feedback report by
itself is not a change; it becomes a change only after going through the
candidate flow in section D.

## G. Independent release cadence

EXPC-GVP releases **independently** from any consuming application
(EXPC-WLK or otherwise). A new Data Pack version does not imply, require,
or wait for a corresponding release of any consumer — see
`docs/00_ARCHITECTURE.md` → "Versioning model" for why Data Pack CalVer,
Builder version, and Schema version are already independent axes; this
independence extends to consumer applications too.

## H. Consumer update contract

A consumer updates by fetching a new GitHub Release and validating it
through the same manifest/SHA-256/schema contract this repository
implements itself (`docs/05_DISTRIBUTION.md`, `docs/06_RELEASE_CONTRACT.md`):

- verify the release tag's CalVer matches `manifest.json: data_pack_version`;
- verify `manifest_contract_version` is recognized;
- verify `schema_version` is one the consumer supports;
- verify the artifact's SHA-256 and `checksums.sha256`.

If a newer release fails verification or uses a schema/manifest-contract
version the consumer does not support, **the consumer should retain its
last known-good, verified pack** rather than adopt a broken or
incompatible one. This document does not implement that consumer-side
logic (no updater exists in this repository) — it states the contract a
future consumer-side updater must honor.

## Related documents

- `docs/00_ARCHITECTURE.md` — versioning model
- `docs/02_VOCABULARY_LAYERS.md` — Global/Domain/Organization/Personal classification
- `docs/03_COLLISION_POLICY.md` — ambiguity/collision review
- `docs/05_DISTRIBUTION.md` — Data Pack package/manifest/checksum contract
- `docs/06_RELEASE_CONTRACT.md` — GitHub Release tag/asset contract
- `SOURCES.md` — provenance/source review policy
- `SECURITY.md` — the hard privacy rules referenced in section C
- `CONTRIBUTING.md` — how to propose a change through the flow in section D
