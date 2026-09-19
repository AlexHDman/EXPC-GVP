"""
CLI entry point.

    py -3.12 -m tools.builder build

Run from the repository root. Exit code 0 on a passing build, non-zero
on any failure (schema, semantic, or blocking-collision), matching the
requirement that this be safe to call from future automation without
that automation existing yet.
"""
import argparse
import sys
from pathlib import Path

from .build import BuildResult, build

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "curated"
DEFAULT_SCHEMA_PATH = REPO_ROOT / "schema" / "gvp.schema.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "dist" / "gvp.json"


def _print_summary(result: BuildResult) -> None:
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build", help="Validate data/curated/*.json and write dist/gvp.json"
    )
    build_parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    build_parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    build_parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))

    args = parser.parse_args(argv)

    if args.command == "build":
        result = build(Path(args.data_dir), Path(args.schema), Path(args.output))
        _print_summary(result)
        return 0 if result.success else 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
