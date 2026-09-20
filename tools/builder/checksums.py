"""
checksums.sha256 format: conventional `sha256sum`-compatible text,
`<hex>  <filename>` per line (two-space separator).

Deliberately covers only gvp.json and manifest.json, never itself --
hashing checksums.sha256 inside checksums.sha256 is circular and
impossible to make stable. manifest.json's own `artifact.sha256` field
covers gvp.json; checksums.sha256 is the one place that also covers
manifest.json, so every file in the package except checksums.sha256 has
its integrity attested somewhere. See docs/05_DISTRIBUTION.md.
"""
from typing import Dict


def format_checksums(file_hashes: Dict[str, str]) -> str:
    """
    `file_hashes`: {filename: sha256_hex}. Sorted by filename so the
    output is deterministic regardless of dict construction order.
    """
    lines = [f"{sha256}  {filename}" for filename, sha256 in sorted(file_hashes.items())]
    return "\n".join(lines) + "\n"


def parse_checksums(text: str) -> Dict[str, str]:
    """Inverse of format_checksums, tolerant of a missing trailing newline."""
    checksums = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        sha256, _, filename = line.partition("  ")
        if not filename:
            continue
        checksums[filename] = sha256
    return checksums
