# Distribution: Data Pack, Manifest, Checksums (Phase 02.0)

**Status: this defines the local, on-disk distribution artifact contract
only.** No GitHub Release, no updater, no network downloader, no consumer
integration exists yet — see "Explicitly out of scope" below.

## Data Pack CalVer

A Data Pack version is a string in the format:

```
YYYY.MM.DD.N
```

e.g. `2026.09.20.1`. `YYYY.MM.DD` must be a real calendar date; `N` is a
positive integer sequence number for same-day releases (`2026.09.20.1`,
`2026.09.20.2`, ...). Validated by `tools/builder/version.py:
validate_data_pack_version`.

The Data Pack version is **always an explicit input** — passed via
`--version` on the `package` CLI command, or as the `data_pack_version`
parameter to `tools/builder/package.py: package()`. The Builder never
generates "today's date" itself and never scans anything (the filesystem,
git history, GitHub) to auto-increment the sequence number. This is
deliberate: a version string is a curator/release decision, not something
inferred, and packaging must not depend on the wall clock or network
access to be reproducible. `tools/builder/version.py` is the one place
that decides whether a given version string is well-formed — the "one
clear version source" the Phase 02.0 brief asked for.

Data Pack version is a **third, independent axis** from the other two —
see `docs/00_ARCHITECTURE.md` → "Versioning model":

| Axis | Current value | Changes when |
|---|---|---|
| Schema version | `0.2.0` | the shape of a vocabulary entity document changes |
| Builder version | `0.2.1-mvp` | the Builder's own capabilities change |
| Data Pack version | e.g. `2026.09.20.1` | a new release of the data is cut |

A new Data Pack version does not imply a new schema or Builder version,
and vice versa — packaging the *same* schema/entities twice under two
different Data Pack versions is normal and expected.

## Package layout

```text
dist/
└── 2026.09.20.1/
    ├── gvp.json
    ├── manifest.json
    └── checksums.sha256
```

This is the layout the Phase 02.0 brief proposed, used as-is — it is
already the simplest structure that satisfies every requirement (one
self-contained directory per version, trivially diffable between
versions, no invented complexity), so no alternative was needed.

No compression and no SQLite pack exist yet (out of scope — see below);
`gvp.json` is written exactly as it is by the plain `build` command (same
serializer, `tools/builder/serialize.py`), just also copied into the
versioned directory alongside its metadata.

## `manifest.json` contract

Built by `tools/builder/manifest.py: build_manifest()`. Minimal by
design — every field exists because some consumer need justifies it,
nothing is included "for completeness":

| Field | Purpose |
|---|---|
| `manifest_contract_version` | Version of *this manifest shape itself* (currently `"1.0"`), independent of schema/Builder/Data-Pack version. A consumer checks this before trusting the rest of the document — see "Manifest contract version" below. |
| `project` | Fixed identifier, `"EXPC-GVP"`. |
| `data_pack_version` | The CalVer string this manifest describes. |
| `schema_version` | The `schema/gvp.schema.json` version every entity in `gvp.json` validated against. |
| `builder_version` | The Builder version (`tools/builder/__init__.py: __builder_version__`) that produced this package. |
| `entity_count` | Number of entities in `gvp.json`, for a cheap sanity check without parsing the whole artifact. |
| `artifact.filename` | `"gvp.json"`. |
| `artifact.sha256` | SHA-256 of `gvp.json`'s exact bytes. |
| `artifact.size_bytes` | `gvp.json`'s exact byte size. |

### What is deliberately NOT in the manifest

- **No timestamp.** The release date is already carried deterministically
  by `data_pack_version` itself (`YYYY.MM.DD.N`). A separate "built at"
  wall-clock field would duplicate that and — worse — would make two
  builds of the *same* version, run at different times, byte-differ for
  no reason. If a future need for build-time provenance beyond the
  version string's own date arises, that is a deliberate future
  manifest-contract-version bump, not something added silently.
- **No absolute paths, username, or hostname.** `artifact.filename` is
  always the bare relative filename (`"gvp.json"`), never a local
  filesystem path.
- **No checksum of `checksums.sha256` itself** — see "Checksum model"
  below for why that would be circular.

### Manifest contract version

`manifest_contract_version` is independent of `data_pack_version`,
`schema_version`, and `builder_version` — it only changes if the *shape
of manifest.json itself* changes in a way old consumers need to know
about, exactly mirroring how `schema_version` works for entity documents
(`docs/01_DATA_SCHEMA.md`). Currently `"1.0"`.
`tools/builder/verify.py: SUPPORTED_MANIFEST_CONTRACT_VERSIONS` is the
allow-list a verifier checks against; an unrecognized contract version
fails verification rather than being guessed at.

## Checksum model (`checksums.sha256`)

Conventional `sha256sum`-compatible text format, one line per file:

```
8ede4b87e9f8c3c0e41894352659b8d084ea9ff87febcaa5b4a1bb1acd88a469  gvp.json
eccddda317ec9b031a15bd7edd76f86ece391dc35fddcab92e187907709d4ac5  manifest.json
```

`<sha256>` then two spaces then the bare filename, lines sorted by
filename. Built/parsed by `tools/builder/checksums.py`.

**Deliberately covers `gvp.json` and `manifest.json` only — never
itself.** Hashing `checksums.sha256` inside `checksums.sha256` is
circular and cannot be made to agree with itself (the hash of the file
changes the moment you write the hash into it). The integrity coverage is
still complete without that: `manifest.json`'s own `artifact.sha256`
field already covers `gvp.json`, and `checksums.sha256` is the one place
that also covers `manifest.json` — so every file in the package except
`checksums.sha256` itself has its integrity attested somewhere, and
`checksums.sha256`'s own integrity is exactly what a consumer trusts by
fetching/reading it directly (the same trust boundary any checksums file
has).

## Reproducibility / determinism

Same source data + same schema + same Builder version + same Data Pack
version **must** produce byte-identical `gvp.json`, `manifest.json`, and
`checksums.sha256`. No filesystem-listing-order dependency (entities are
sorted by `id`; checksum lines are sorted by filename), no current-time
dependency (no timestamps anywhere in the package), no random
identifiers in any file's *content* (a random component is used only for
the disposable staging directory's *name* during publish — see below —
which is never part of the published package). Verified in
`tests/test_package.py:
test_two_independent_package_builds_are_byte_identical`.

## Safe / staged / atomic package publish

Implemented in `tools/builder/package.py: _stage_and_publish`. Flow:

```text
staging directory (dist/.pkg-staging-<random>/)
        ↓
write gvp.json, manifest.json, checksums.sha256 into staging
        ↓
self-verify the staged package (tools/builder/verify.py)
        ↓
publish (see "Windows directory-replace note" below)
```

If any step fails, the disposable staging directory is removed and
nothing under the final `dist/<version>/` path is ever touched.

### Windows directory-replace note

An atomic rename (`os.replace`/`Path.replace`) can move a directory into
a path that does not yet exist, but — unlike POSIX, which can atomically
replace an *empty* destination directory — Windows cannot atomically
replace an existing, **non-empty** destination directory in one
filesystem operation. Rather than emulating a cross-platform
transactional directory replace (explicitly out of scope per the Phase
02.0 brief — "do not over-engineer cross-platform transactional
filesystem semantics"), this treats a Data Pack version as **immutable
once published**:

- `dist/<version>/` does not exist yet → plain atomic rename of the
  staging directory into place. The common, first-publish case.
- `dist/<version>/` already exists and its 3 files are byte-identical to
  the freshly-staged ones → treated as a harmless no-op (e.g. re-running
  `package` for the same version against unchanged source data). The
  existing directory is left completely untouched; only the disposable
  staging directory is removed.
- `dist/<version>/` already exists with **different** content → refused
  with a non-zero exit code. Reusing the same CalVer version string for
  two different datasets would be a genuine integrity violation (the
  version would no longer uniquely identify one set of bytes), so this is
  treated as a version-immutability violation, not something to silently
  overwrite. The existing, previously-valid package is left completely
  untouched — this is also exactly what "a failed package build must not
  corrupt an existing valid package of that version" means in practice.

## Verification algorithm

`tools/builder/verify.py: verify_package(package_dir)` checks a package
directory **standalone** — from its own files only, without rebuilding
from `data/curated/` or even needing `schema/gvp.schema.json`:

1. All three required files exist.
2. `manifest.json` parses as JSON.
3. `manifest_contract_version` is one this Builder version recognizes.
4. `gvp.json`'s actual SHA-256 matches `manifest.json`'s `artifact.sha256`.
5. `gvp.json`'s actual byte size matches `manifest.json`'s `artifact.size_bytes`.
6. `gvp.json` parses as JSON, and its `entities` count matches `manifest.json`'s `entity_count`.
7. `gvp.json`'s `schema_version` matches `manifest.json`'s `schema_version` (coherence between the two files).
8. `checksums.sha256`'s hashes for `gvp.json` and `manifest.json` match their actual bytes.

Any failure is collected (not just the first) and reported; `VerifyResult.success` is `True` only if every check passed. This is intentionally reusable — a future updater/consumer can call the same function to validate a package it already has on disk before trusting/installing it, without needing this repository's source data or schema at all. It performs no network access and does not fetch, install, or compare against any other version.

## CLI

```
py -3.12 -m tools.builder package --version 2026.09.20.1
py -3.12 -m tools.builder verify dist/2026.09.20.1
```

Both exit `0` on success, non-zero on any failure (invalid CalVer,
underlying build failure, packaging failure, or verification failure).
`build` (existing, unchanged) still exits `0`/non-zero the same way.

## Explicitly out of scope (Phase 02.0)

Not implemented, and not to be assumed working:

- SQLite (or any other compiled) data pack
- compression of the package (not needed for 15 entities)
- GitHub Releases or Git tags
- GitHub Actions / CI wiring
- any network access (release discovery, downloading, uploading)
- an auto-updater or any consumer-side install/update logic
- EXPC-WLK integration
- signing / public-key infrastructure — SHA-256 integrity checking is
  the full extent of Phase 02.0's integrity model
- external dataset import, nightly automation

## Future GitHub Release relationship

Not implemented yet, but the shape of `dist/<version>/` is deliberately
what a future GitHub Release's uploaded assets would be — `gvp.json`,
`manifest.json`, and `checksums.sha256` as three separate release assets
for that tag/version. `verify_package()` is written to only need a local
directory, so it would apply unchanged to a downloaded-and-extracted
release without modification. None of that (creating the release,
downloading assets, wiring a tag to a Data Pack version) exists yet.

Phase 02.1 (`docs/06_RELEASE_CONTRACT.md`) now defines exactly how a tag
name maps to this Data Pack version (`gvp-<CalVer>`) and adds a local,
offline `release-check` command that validates a package directory
against a tag by re-using `verify_package()` above — still no GitHub API,
network access, or actual tag/Release creation.
