# GitHub Release Contract (Phase 02.1)

**Status: this defines and locally validates the *contract* a future
GitHub Release must satisfy. It does not publish anything.** No GitHub
API client, no GitHub Actions/CI, no network access, no actual Git tag,
and no actual GitHub Release exist yet or are created by this phase. See
"Explicitly out of scope" below.

Phase 02.1 builds directly on the Phase 02.0 local Data Pack
(`docs/05_DISTRIBUTION.md`) — it adds a naming convention for how that
package would map onto a Git tag / GitHub Release, and one small local
command (`release-check`) that validates a package directory against a
tag, offline, by re-using Phase 02.0's own verification.

## Release version / tag contract

A GitHub Release is named directly from the Data Pack CalVer it carries —
no separate release-numbering scheme is introduced:

| | Value |
|---|---|
| Data Pack version | `2026.09.20.1` |
| Git tag | `gvp-2026.09.20.1` |
| Release title | `EXPC-GVP 2026.09.20.1` |

Rules:

- The tag prefix is exactly `gvp-` (lowercase, literal).
- The suffix after the prefix must be a well-formed Data Pack CalVer,
  `YYYY.MM.DD.N` (`tools/builder/version.py: validate_data_pack_version`).
- The tag's CalVer must exactly match the package's own
  `manifest.json: data_pack_version` — a tag names *the* package it is
  attached to, not merely a valid-looking version string.
- No fourth version axis is introduced. This is Data Pack CalVer, reused
  as-is; it is not a new "release version" independent of the three axes
  in `docs/00_ARCHITECTURE.md` → "Versioning model".
- Malformed or non-GVP tags (wrong/missing prefix, invalid CalVer suffix,
  or any unrelated repository tag) must be ignored by future discovery
  logic, never guessed at or coerced into a version.

Implemented as pure, local, offline functions in
`tools/builder/release.py`:

- `release_tag(data_pack_version)` / `release_title(data_pack_version)` —
  Data Pack CalVer → tag / title string.
- `parse_release_tag(tag)` — the inverse: validates a tag against the
  contract above and returns its CalVer, or raises `ReleaseTagError` for
  anything that doesn't match (so a future discovery loop can catch
  exactly that one exception type and skip the tag).
- `is_valid_release_tag(tag)` — non-raising `bool` wrapper over the same
  check, for filtering a list of tags.

## Release assets

A GitHub Release for a given tag contains exactly the three files the
Phase 02.0 `package` command already produced for that Data Pack version
— nothing regenerated, nothing modified at publish time:

```text
gvp.json
manifest.json
checksums.sha256
```

No ZIP or other compression, and no SQLite pack — the assets are exactly
what `dist/<CalVer>/` already holds (`docs/05_DISTRIBUTION.md` → "Package
layout"). This mirrors that document's own "Future GitHub Release
relationship" section: the local package's shape *is* the release-asset
shape, by design.

## Release discovery contract

For a future consumer (not implemented — no GitHub API/network access
exists) enumerating which GitHub Releases are EXPC-GVP Data Pack
releases:

- Only tags matching `gvp-<valid-CalVer>` are GVP Data Pack releases
  (`is_valid_release_tag`).
- Draft releases are ignored.
- Prerelease releases are ignored by the normal stable-update path.
- Malformed tags are ignored (skip, don't fail discovery entirely).
- Unrelated repository tags are ignored.
- Version comparison/ordering uses **parsed numeric CalVer components,
  never lexical string ordering**. A Data Pack's sequence number `N` has
  no fixed width (`YYYY.MM.DD.N`, `N` is `\d+`), so a naive string
  comparison gets same-day releases backwards once `N` reaches two
  digits: lexically `"2026.09.20.10" < "2026.09.20.9"` (because `'1' <
  '9'`), even though `10 > 9`. `tools/builder/version.py:
  parse_calver_components` parses a CalVer string into an
  `(year, month, day, sequence)` int tuple for correct comparison, and
  `tools/builder/release.py: compare_calver(a, b)` compares two CalVer
  strings that way (returns `-1`/`0`/`1`). E.g.
  `compare_calver("2026.10.01.1", "2026.09.30.9") == 1`.

## Compatibility contract

A future consumer must accept a Data Pack only after **all** of the
following hold, in this order (fail-safe — reject on the first
unsatisfied check, never guess):

1. `manifest_contract_version` is recognized by the consumer.
2. The Data Pack CalVer is valid.
3. The tag's CalVer equals `manifest.json: data_pack_version`.
4. `schema_version` is one the consumer supports.
5. All required package assets exist.
6. The artifact's SHA-256 matches `manifest.json: artifact.sha256`.
7. `checksums.sha256` matches the actual file bytes.
8. Full package verification passes
   (`tools/builder/verify.py: verify_package`).

An unrecognized/incompatible manifest-contract or schema **major**
version must be rejected outright — no compatibility matrix, shimming, or
partial acceptance. Checks 4–8 above are exactly what
`release_check` (below) already performs by re-using `verify_package`;
this list is the contract a *network-aware* future consumer would extend
with checks 1–3 first (which need the tag, something `verify_package`
alone doesn't see).

## Manual publication procedure (documentation only)

Phase 02.1 documents this procedure. None of the following steps are
automated or executed by this phase — no tag, no Release, and no push of
either was created:

```text
Builder package                (tools/builder/package.py — Phase 02.0)
      ↓
local verify                   (tools/builder/verify.py — Phase 02.0)
      ↓
release candidate check        (tools/builder/release.py — Phase 02.1)
      ↓
create Git tag                 (manual; gvp-<CalVer>; NOT automated)
      ↓
create GitHub Release          (manual; NOT automated)
      ↓
attach exact 3 verified artifacts   (gvp.json, manifest.json, checksums.sha256)
      ↓
verify asset names              (must match the three filenames exactly)
```

## Local release-candidate check

`tools/builder/release.py: release_check(tag, package_dir)` — and the
`release-check` CLI subcommand — validate a package directory against a
tag, entirely locally:

```
py -3.12 -m tools.builder release-check --tag gvp-2026.09.20.1 dist\2026.09.20.1
```

Checks, in order (stops at the first failure):

1. `tag` matches the `gvp-<CalVer>` contract (`parse_release_tag`).
2. The package passes full standalone verification
   (`verify.py: verify_package`) — this alone covers "all three required
   files present" plus every integrity/tamper check from
   `docs/05_DISTRIBUTION.md` → "Verification algorithm".
3. The tag's CalVer exactly equals the verified manifest's
   `data_pack_version`.

Deliberately thin: `release_check` is orchestration around the existing
`verify_package`, not a second verification engine — it adds exactly one
new fact (`tag` ↔ `manifest.json` agreement) on top of what Phase 02.0
already checks. No GitHub API call, no network access. Exit code `0` on
success, non-zero on any failure, same convention as `build`/`package`/
`verify`.

## Explicitly out of scope (Phase 02.1)

Not implemented, and not to be assumed working:

- a GitHub API client of any kind
- GitHub Actions / CI wiring
- automatic release discovery or publishing over a network
- an auto-updater or network downloader
- EXPC-WLK or any other consumer integration
- SQLite (or any other compiled) data pack
- compression of the package
- signing / public-key infrastructure
- external vocabulary import, nightly automation
- creating an actual Git tag or an actual GitHub Release (this phase only
  defines and locally validates the contract those would need to satisfy)

## Related documents

- `docs/00_ARCHITECTURE.md` — the three independent version axes this
  contract reuses without adding a fourth
- `docs/04_BUILDER.md` — the `build` command `release-check` sits beside
- `docs/05_DISTRIBUTION.md` — the local Data Pack contract (manifest,
  checksums, `package`/`verify`) this phase builds on and re-uses
