from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import build_inventory
from .report import write_dot, write_inventory, write_markdown
from .scanner import index_copybooks, scan_tree


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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "scan":
        source = args.source.resolve()
        units = scan_tree(source)
        search_roots = [source, *(p.resolve() for p in args.copybook_path)]
        copybook_index = index_copybooks(search_roots)
        inventory = build_inventory(units, copybook_index)

        write_inventory(inventory, args.output)
        write_markdown(units, inventory, args.output)
        write_dot(units, inventory, args.output)

        metrics = inventory["metrics"]
        print(
            f"Scanned {metrics['unit_count']} units "
            f"({metrics['program_count']} programs, {metrics['copybook_count']} copybooks) "
            f"into {args.output}"
        )
        unresolved = metrics["unresolved_call_count"] + metrics["unresolved_copybook_count"]
        if unresolved:
            print(
                f"  {metrics['unresolved_call_count']} unresolved CALLs, "
                f"{metrics['unresolved_copybook_count']} unresolved copybooks"
            )


if __name__ == "__main__":
    main()
