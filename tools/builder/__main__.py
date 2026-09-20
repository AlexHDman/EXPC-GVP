"""
CLI entry point.

    py -3.12 -m tools.builder build
    py -3.12 -m tools.builder package --version 2026.09.20.1
    py -3.12 -m tools.builder verify dist\\2026.09.20.1
    py -3.12 -m tools.builder release-check --tag gvp-2026.09.20.1 dist\\2026.09.20.1

Run from the repository root. Exit code 0 on success, non-zero on any
failure (schema, semantic, blocking-collision, invalid CalVer, packaging,
verification, or release-check failure), matching the requirement that
this be safe to call from future automation without that automation
existing yet. `release-check` is local-only (no GitHub API, no network)
-- see docs/06_RELEASE_CONTRACT.md.
"""
import argparse
import sys
from pathlib import Path

from .build import BuildResult, build
from .package import PackageResult, package
from .release import ReleaseCheckResult, release_check
from .verify import VerifyResult, verify_package

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "curated"
DEFAULT_SCHEMA_PATH = REPO_ROOT / "schema" / "gvp.schema.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "dist" / "gvp.json"
DEFAULT_DIST_DIR = REPO_ROOT / "dist"


def _print_build_summary(result: BuildResult) -> None:
    print("EXPC-GVP Builder")
    print(f"Schema: {result.schema_version}")
    print(f"Entities: {result.entity_count}")

    schema_ok = not result.schema_errors
    print(f"Schema validation: {'PASS' if schema_ok else 'FAIL'}")
    for err in result.schema_errors:
        print(f"  - {err}")
    if not schema_ok:
        print("BUILD: FAIL")
        return

    semantic_ok = not result.semantic_errors
    print(f"Semantic validation: {'PASS' if semantic_ok else 'FAIL'}")
    for err in result.semantic_errors:
        print(f"  - {err}")
    if not semantic_ok:
        print("BUILD: FAIL")
        return

    print(
        f"Collisions: {len(result.blocking_collisions)} blocking / "
        f"{len(result.contextual_collisions)} contextual"
    )
    for b in result.blocking_collisions:
        print(f"  - BLOCKING: {b}")

    if result.success:
        print(f"Output: {result.output_path}")
        print("BUILD: PASS")
    else:
        print("BUILD: FAIL")


def _print_package_summary(result: PackageResult) -> None:
    print("EXPC-GVP Data Pack")
    print(f"Version: {result.data_pack_version}")
    if not result.success:
        for err in result.errors:
            print(f"  - {err}")
        print("PACKAGE: FAIL")
        return

    print(f"Schema: {result.schema_version}")
    print(f"Builder: {result.builder_version}")
    print(f"Entities: {result.entity_count}")
    print(f"Artifact SHA-256: {result.artifact_sha256}")
    print("Manifest: PASS")
    print("Checksums: PASS")
    print(f"Package: {result.package_dir}")
    if result.reused_existing:
        print("(version already existed with identical content -- no-op)")
    print("PACKAGE: PASS")


def _print_verify_summary(result: VerifyResult) -> None:
    print("EXPC-GVP Data Pack Verification")
    print(f"Package: {result.package_dir}")
    if result.manifest:
        print(f"Data Pack version: {result.manifest.get('data_pack_version')}")
        print(f"Schema version: {result.manifest.get('schema_version')}")
        print(f"Entities: {result.manifest.get('entity_count')}")
    for err in result.errors:
        print(f"  - {err}")
    print("VERIFY: PASS" if result.success else "VERIFY: FAIL")


def _print_release_check_summary(result: ReleaseCheckResult) -> None:
    print("EXPC-GVP Release Candidate Check")
    print(f"Tag: {result.tag}")
    if result.data_pack_version:
        print(f"Data Pack version: {result.data_pack_version}")
    print(f"Package: {result.package_dir}")
    for err in result.errors:
        print(f"  - {err}")
    print("RELEASE-CHECK: PASS" if result.success else "RELEASE-CHECK: FAIL")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build", help="Validate data/curated/*.json and write dist/gvp.json"
    )
    build_parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    build_parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    build_parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))

    package_parser = subparsers.add_parser(
        "package", help="Build a versioned Data Pack under dist/<version>/"
    )
    package_parser.add_argument(
        "--version", required=True, help="Data Pack CalVer, e.g. 2026.09.20.1"
    )
    package_parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    package_parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    package_parser.add_argument("--dist-dir", default=str(DEFAULT_DIST_DIR))

    verify_parser = subparsers.add_parser(
        "verify", help="Verify an existing dist/<version>/ package directory"
    )
    verify_parser.add_argument("package_dir", help="Path to the package directory to verify")

    release_check_parser = subparsers.add_parser(
        "release-check",
        help="Validate a local package directory as a release candidate for a Git tag",
    )
    release_check_parser.add_argument(
        "--tag", required=True, help="Git tag, e.g. gvp-2026.09.20.1"
    )
    release_check_parser.add_argument("package_dir", help="Path to the package directory to check")

    args = parser.parse_args(argv)

    if args.command == "build":
        result = build(Path(args.data_dir), Path(args.schema), Path(args.output))
        _print_build_summary(result)
        return 0 if result.success else 1

    if args.command == "package":
        result = package(
            Path(args.data_dir), Path(args.schema), Path(args.dist_dir), args.version
        )
        _print_package_summary(result)
        return 0 if result.success else 1

    if args.command == "verify":
        result = verify_package(Path(args.package_dir))
        _print_verify_summary(result)
        return 0 if result.success else 1

    if args.command == "release-check":
        result = release_check(args.tag, Path(args.package_dir))
        _print_release_check_summary(result)
        return 0 if result.success else 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
