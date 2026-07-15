from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

PROGRAM_ID = re.compile(r"\bPROGRAM-ID\.\s+([A-Z0-9_-]+)", re.IGNORECASE)
COPY = re.compile(r"\bCOPY\s+['\"]?([A-Z0-9_-]+(?:\.[A-Z0-9_-]+)*)['\"]?(?=\s|\.)", re.IGNORECASE)
CALL = re.compile(r"\bCALL\s+['\"]([A-Z0-9_.-]+)['\"]", re.IGNORECASE)
PARAGRAPH = re.compile(r"^\s{0,11}([A-Z0-9][A-Z0-9-]*)\.\s*$", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class CobolUnit:
    path: str
    kind: str
    program_id: str | None
    copybooks: list[str]
    calls: list[str]
    paragraphs: list[str]
    line_count: int
    byte_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_source(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if len(line) >= 7 and line[6] in {"*", "/"}:
            continue
        lines.append(line[7:72] if len(line) > 7 else line)
    return "\n".join(lines)


def scan_file(path: Path, root: Path) -> CobolUnit:
    raw = path.read_text(encoding="utf-8", errors="replace")
    source = normalize_source(raw)
    program_match = PROGRAM_ID.search(source)
    suffix = path.suffix.lower()
    kind = "copybook" if suffix in {".cpy", ".copy"} else "program"
    return CobolUnit(
        path=str(path.relative_to(root)),
        kind=kind,
        program_id=program_match.group(1).upper() if program_match else None,
        copybooks=sorted({match.upper() for match in COPY.findall(source)}),
        calls=sorted({match.upper() for match in CALL.findall(source)}),
        paragraphs=sorted({match.upper() for match in PARAGRAPH.findall(source)}),
        line_count=len(raw.splitlines()),
        byte_count=len(raw.encode("utf-8")),
    )


def scan_tree(root: Path) -> list[CobolUnit]:
    extensions = {".cbl", ".cob", ".cobol", ".cpy", ".copy"}
    return [scan_file(path, root) for path in sorted(root.rglob("*")) if path.suffix.lower() in extensions]
