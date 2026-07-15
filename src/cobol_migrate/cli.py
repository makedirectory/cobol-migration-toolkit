from __future__ import annotations

import argparse
from pathlib import Path

from .report import write_dot, write_inventory, write_markdown
from .scanner import scan_tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cobol-migrate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan a COBOL source tree")
    scan.add_argument("source", type=Path)
    scan.add_argument("--output", type=Path, default=Path("build"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "scan":
        source = args.source.resolve()
        units = scan_tree(source)
        write_inventory(units, args.output)
        write_markdown(units, args.output)
        write_dot(units, args.output)
        print(f"Scanned {len(units)} units into {args.output}")


if __name__ == "__main__":
    main()
