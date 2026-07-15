from __future__ import annotations

import json
from pathlib import Path

from .scanner import CobolUnit


def write_inventory(units: list[CobolUnit], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = {"units": [unit.to_dict() for unit in units]}
    (output / "inventory.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(units: list[CobolUnit], output: Path) -> None:
    known = {unit.program_id for unit in units if unit.program_id}
    lines = ["# COBOL Inventory", "", f"Scanned units: **{len(units)}**", ""]
    for unit in units:
        lines.extend([
            f"## `{unit.path}`",
            "",
            f"- Type: `{unit.kind}`",
            f"- Program ID: `{unit.program_id or 'unknown'}`",
            f"- Lines: {unit.line_count}",
            f"- COPY dependencies: {', '.join(unit.copybooks) or 'none'}",
            f"- CALL targets: {', '.join(unit.calls) or 'none'}",
            f"- Unresolved static calls: {', '.join(c for c in unit.calls if c not in known) or 'none'}",
            f"- Paragraphs: {', '.join(unit.paragraphs) or 'none'}",
            "",
        ])
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def write_dot(units: list[CobolUnit], output: Path) -> None:
    lines = ["digraph cobol_dependencies {", "  rankdir=LR;"]
    for unit in units:
        source = unit.program_id or unit.path
        lines.append(f'  "{source}" [shape=box];')
        for target in unit.calls:
            lines.append(f'  "{source}" -> "{target}" [label="CALL"];')
        for target in unit.copybooks:
            lines.append(f'  "{source}" -> "{target}" [label="COPY", style=dashed];')
    lines.append("}")
    (output / "dependencies.dot").write_text("\n".join(lines) + "\n", encoding="utf-8")
