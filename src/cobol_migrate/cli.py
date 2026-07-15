from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from .analysis import build_inventory
from .config import Config, find_config, load_config
from .plugins import ScanContext, discover_analyzers, run_analyzers, select_analyzers
from .report import write_dot, write_html, write_inventory, write_markdown
from .scanner import index_copybooks, scan_tree

FORMATS = ("json", "md", "dot", "html")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cobol-migrate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan a COBOL source tree")
    scan.add_argument("source", type=Path)
    scan.add_argument("--output", type=Path, default=None)
    scan.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="FILE",
        help=f"path to a config file (default: auto-discover {'.cobolmigrate.toml'})",
    )
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
    scan.add_argument(
        "--analyzers",
        action="append",
        metavar="{all,none,<name>}",
        help="which analyzer plugins to run; repeatable (default: all discovered)",
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
    analyzers: list[str] | None = None,
    extensions: set[str] | None = None,
    options: dict[str, object] | None = None,
) -> int:
    source = source.resolve()
    units = scan_tree(source, extensions)
    search_roots = [source, *(p.resolve() for p in copybook_paths)]
    copybook_index = index_copybooks(search_roots, extensions)

    selected = select_analyzers(discover_analyzers(), analyzers)
    ctx = ScanContext(units=units, copybook_index=copybook_index, root=source, options=options or {})
    analyses = run_analyzers(selected, ctx)
    analyzer_names = [a.name for a in selected]
    inventory = build_inventory(units, copybook_index, analyses, analyzer_names)

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
    if analyzer_names:
        print(f"  analyzers: {', '.join(analyzer_names)}")
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


@dataclass
class ResolvedScan:
    output: Path
    copybook_paths: list[Path]
    formats: list[str]
    strict: bool
    analyzers: list[str] | None
    extensions: set[str] | None
    options: dict[str, object]


def merge_config(args: argparse.Namespace, config: Config) -> ResolvedScan:
    """CLI flags win over config-file values; the file supplies defaults."""
    base = config.path.parent if config.path else Path.cwd()
    copybook_paths = [(base / p).resolve() for p in config.copybook_paths] + list(args.copybook_path)
    return ResolvedScan(
        output=args.output or (Path(config.output) if config.output else Path("build")),
        copybook_paths=copybook_paths,
        formats=resolve_formats(args.format if args.format else config.formats),
        strict=args.strict or config.strict,
        analyzers=args.analyzers if args.analyzers else config.analyzers,
        extensions=config.extensions,
        options=config.options,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "scan":
        source = args.source.resolve()
        config = load_config(find_config(source, args.config))
        if config.path:
            print(f"Using config {config.path}")
        r = merge_config(args, config)
        code = run_scan(source, r.output, r.copybook_paths, r.formats, r.strict, r.analyzers, r.extensions, r.options)
        raise SystemExit(code)


if __name__ == "__main__":
    main()
