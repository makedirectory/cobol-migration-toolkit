from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .analysis import Metrics, build_inventory
from .config import Config, find_config, load_config
from .plugins import (
    ScanContext,
    discover_analyzers,
    discover_inventory_analyzers,
    run_analyzers,
    run_inventory_analyzers,
    select_analyzers,
)
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
    scan.add_argument(
        "--fail-on",
        action="append",
        metavar="METRIC[:MAX]",
        help="exit non-zero if a metric exceeds MAX (default 0); repeatable. "
        "e.g. --fail-on unresolved_call_count --fail-on max_fan_in:20",
    )

    schema = subparsers.add_parser("schema", help="print the inventory.json JSON Schema")
    schema.add_argument("--output", type=Path, default=None, metavar="FILE")
    return parser


def evaluate_fail_on(metrics: Metrics, checks: list[str]) -> list[str]:
    """Return a list of failure messages for any `METRIC[:MAX]` check that is exceeded."""
    failures: list[str] = []
    md: dict[str, object] = dict(metrics)
    for check in checks:
        key, sep, raw_max = check.partition(":")
        try:
            threshold = int(raw_max) if sep else 0
        except ValueError:
            failures.append(f"--fail-on '{check}': threshold must be an integer")
            continue
        if key not in md:
            failures.append(f"--fail-on '{key}': unknown metric")
            continue
        value = md[key]
        if isinstance(value, list):
            actual = len(value)
        elif isinstance(value, int):
            actual = value
        else:
            failures.append(f"--fail-on '{key}': not a numeric metric")
            continue
        if actual > threshold:
            failures.append(f"{key}={actual} exceeds {threshold}")
    return failures


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
    fail_on: list[str] | None = None,
) -> int:
    source = source.resolve()
    units = scan_tree(source, extensions)
    search_roots = [source, *(p.resolve() for p in copybook_paths)]
    copybook_index = index_copybooks(search_roots, extensions)

    selected = select_analyzers(discover_analyzers(), analyzers)
    inventory_selected = select_analyzers(discover_inventory_analyzers(), analyzers)
    ctx = ScanContext(units=units, copybook_index=copybook_index, root=source, options=options or {})
    analyses = run_analyzers(selected, ctx)
    analyzer_names = [a.name for a in selected]
    inventory = build_inventory(units, copybook_index, analyses, analyzer_names)
    # Inventory analyzers run after per-unit analyses are merged, so they can aggregate them.
    inventory["reports"] = run_inventory_analyzers(inventory_selected, inventory, ctx)

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
    if inventory["reports"]:
        print(f"  reports: {', '.join(sorted(inventory['reports']))}")
    unresolved = metrics["unresolved_call_count"] + metrics["unresolved_copybook_count"]
    if unresolved:
        print(
            f"  {metrics['unresolved_call_count']} unresolved CALLs, "
            f"{metrics['unresolved_copybook_count']} unresolved copybooks"
        )
    failures: list[str] = []
    if strict and unresolved:
        failures.append(f"unresolved dependencies (--strict): {unresolved}")
    if fail_on:
        failures.extend(evaluate_fail_on(metrics, fail_on))
    if failures:
        for failure in failures:
            print(f"fail-on: {failure}", file=sys.stderr)
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
    fail_on: list[str] | None


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
        fail_on=args.fail_on if args.fail_on else config.fail_on,
    )


def run_schema(output: Path | None) -> int:
    from .schema import inventory_schema

    text = json.dumps(inventory_schema(), indent=2) + "\n"
    if output is not None:
        output.write_text(text, encoding="utf-8")
        print(f"Wrote inventory JSON Schema to {output}")
    else:
        print(text, end="")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "schema":
        raise SystemExit(run_schema(args.output))
    if args.command == "scan":
        source = args.source.resolve()
        config = load_config(find_config(source, args.config))
        if config.path:
            print(f"Using config {config.path}")
        r = merge_config(args, config)
        code = run_scan(
            source,
            r.output,
            r.copybook_paths,
            r.formats,
            r.strict,
            r.analyzers,
            r.extensions,
            r.options,
            r.fail_on,
        )
        raise SystemExit(code)


if __name__ == "__main__":
    main()
