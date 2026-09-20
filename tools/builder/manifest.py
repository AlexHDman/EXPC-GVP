"""
manifest.json contract (Phase 02.0). See docs/05_DISTRIBUTION.md for the
full field-by-field writeup; this module is the single source of truth
for what a manifest actually contains.

Deliberately excluded, by design:
  - any wall-clock timestamp. The release date is already carried
    deterministically by the CalVer `data_pack_version` itself
    (YYYY.MM.DD.N) -- a separate "built at" timestamp would only
    duplicate that and would break byte-identical reproducibility for
    two builds of the same version run at different times.
  - absolute paths, username, hostname, or any other local-machine detail.
  - the checksum of checksums.sha256 itself -- see
    tools/builder/checksums.py for why (avoiding circular hashing).

"Compatibility information needed by a consumer" (per the Phase 02.0
brief) is `schema_version` (how to interpret the entities inside
gvp.json) plus `manifest_contract_version` (how to interpret this
manifest itself) -- no separate/redundant compatibility field is added
on top of those two.
"""
PROJECT_ID = "EXPC-GVP"
MANIFEST_CONTRACT_VERSION = "1.0"


def build_manifest(
    *,
    data_pack_version: str,
    schema_version: str,
    builder_version: str,
    entity_count: int,
    artifact_filename: str,
    artifact_sha256: str,
    artifact_size_bytes: int,
) -> dict:
    """
    Field order here is the field order in the written manifest.json
    (json.dump does not reorder dict keys) -- kept fixed and logical
    (identity -> versions -> content -> artifact) for human readability,
    not alphabetical.
    """
    return {
        "manifest_contract_version": MANIFEST_CONTRACT_VERSION,
        "project": PROJECT_ID,
        "data_pack_version": data_pack_version,
        "schema_version": schema_version,
        "builder_version": builder_version,
        "entity_count": entity_count,
        "artifact": {
            "filename": artifact_filename,
            "sha256": artifact_sha256,
            "size_bytes": artifact_size_bytes,
        },
    }
