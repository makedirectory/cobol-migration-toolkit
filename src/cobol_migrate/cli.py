from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analysis import build_inventory
from .report import write_dot, write_html, write_inventory, write_markdown
from .scanner import index_copybooks, scan_tree

FORMATS = ("json", "md", "dot", "html")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cobol-migrate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan a COBOL source tree")
    scan.add_argument("source", type=Path)
    scan.add_argument("--output", type=Path, default=Path("build"))
    scan.add_argument(
        "--copybook-path",
        type=Path,
        action="append",
        default=[],
        metavar="DIR",
        help="additional directory to resolve COPY members from (repeatable)",
    )
    scan.add_argument(
        "--format",
        action="append",
        choices=[*FORMATS, "all"],
        metavar="{json,md,dot,html,all}",
        help="output format(s) to emit; repeatable (default: all)",
    )
    scan.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any CALL or copybook dependency is unresolved",
    )
    return parser


def resolve_formats(selected: list[str] | None) -> list[str]:
    if not selected or "all" in selected:
        return list(FORMATS)
    return [fmt for fmt in FORMATS if fmt in selected]


def run_scan(
    source: Path,
    output: Path,
    copybook_paths: list[Path],
    formats: list[str],
    strict: bool,
) -> int:
    source = source.resolve()
    units = scan_tree(source)
    search_roots = [source, *(p.resolve() for p in copybook_paths)]
    inventory = build_inventory(units, index_copybooks(search_roots))

    if "json" in formats:
        write_inventory(inventory, output)
    if "md" in formats:
        write_markdown(units, inventory, output)
    if "dot" in formats:
        write_dot(units, inventory, output)
    if "html" in formats:
        write_html(units, inventory, output)

    metrics = inventory["metrics"]
    print(
        f"Scanned {metrics['unit_count']} units "
        f"({metrics['program_count']} programs, {metrics['copybook_count']} copybooks) "
        f"into {output}"
    )
    unresolved = metrics["unresolved_call_count"] + metrics["unresolved_copybook_count"]
    if unresolved:
        print(
            f"  {metrics['unresolved_call_count']} unresolved CALLs, "
            f"{metrics['unresolved_copybook_count']} unresolved copybooks"
        )
    if strict and unresolved:
        print("Failing due to unresolved dependencies (--strict).", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "scan":
        code = run_scan(
            args.source,
            args.output,
            args.copybook_path,
            resolve_formats(args.format),
            args.strict,
        )
        raise SystemExit(code)


if __name__ == "__main__":
    main()
