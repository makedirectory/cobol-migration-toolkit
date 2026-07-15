from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

PROGRAM_ID = re.compile(r"\bPROGRAM-ID\.\s+([A-Z0-9_-]+)", re.IGNORECASE)
COPY = re.compile(r"\bCOPY\s+['\"]?([A-Z0-9_-]+(?:\.[A-Z0-9_-]+)*)['\"]?(?=\s|\.)", re.IGNORECASE)
COPY_REPLACING = re.compile(
    r"\bCOPY\s+['\"]?([A-Z0-9_-]+(?:\.[A-Z0-9_-]+)*)['\"]?[^.]*?\bREPLACING\b",
    re.IGNORECASE | re.DOTALL,
)
CALL = re.compile(r"\bCALL\s+['\"]([A-Z0-9_.-]+)['\"]", re.IGNORECASE)
PARAGRAPH = re.compile(r"^\s{0,11}([A-Z0-9][A-Z0-9-]*)\.\s*$", re.IGNORECASE | re.MULTILINE)

SOURCE_EXTENSIONS = {".cbl", ".cob", ".cobol"}
COPYBOOK_EXTENSIONS = {".cpy", ".copy"}
ALL_EXTENSIONS = SOURCE_EXTENSIONS | COPYBOOK_EXTENSIONS

# Fixed-format layout (1-indexed columns):
#   1-6   sequence area   7  indicator   8-72  program text   73+ ignored
_SEQ_AREA = slice(0, 6)
_INDICATOR = 6
_TEXT_AREA = slice(7, 72)
_COMMENT_INDICATORS = {"*", "/"}
_SKIP_INDICATORS = {"*", "/", "D", "d", "$"}  # comment, debug, and vendor directive lines


@dataclass(frozen=True)
class CobolUnit:
    path: str
    kind: str
    source_format: str
    program_id: str | None
    copybooks: list[str]
    copy_replacing: list[str]
    calls: list[str]
    paragraphs: list[str]
    line_count: int
    byte_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def detect_format(text: str) -> str:
    """Best-effort detection of fixed vs free source format.

    Honors an explicit ``>>SOURCE FORMAT`` directive; otherwise votes line by line
    on whether content respects the fixed-format sequence/indicator columns.
    """
    lowered = text.lower()
    if ">>source format free" in lowered:
        return "free"
    if ">>source format fixed" in lowered:
        return "fixed"

    fixed_votes = 0
    free_votes = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        seq = line[_SEQ_AREA]
        if seq.strip() and not seq.strip().isdigit():
            # real code (not a sequence number) sitting in columns 1-6 → free format
            free_votes += 1
        elif len(line) > _INDICATOR and line[_INDICATOR] not in " *-/dD$":
            # something other than a valid indicator character in column 7 → likely free
            free_votes += 1
        else:
            fixed_votes += 1
    return "free" if free_votes > fixed_votes else "fixed"


def _normalize_fixed(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        indicator = line[_INDICATOR] if len(line) > _INDICATOR else " "
        if indicator in _SKIP_INDICATORS:
            continue
        area = line[_TEXT_AREA] if len(line) > _INDICATOR else ""
        if indicator == "-" and out:
            # continuation line: concatenate onto the previous logical line
            out[-1] = out[-1].rstrip() + area.strip()
        else:
            out.append(area)
    return "\n".join(out)


def _normalize_free(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("*>") or stripped.startswith("*"):
            continue  # full-line comment
        inline = line.find("*>")
        out.append(line[:inline] if inline != -1 else line)
    return "\n".join(out)


def normalize_source(text: str, source_format: str | None = None) -> str:
    """Strip comments/columns so extraction regexes see only program text."""
    fmt = source_format or detect_format(text)
    return _normalize_free(text) if fmt == "free" else _normalize_fixed(text)


def scan_file(path: Path, root: Path) -> CobolUnit:
    raw = path.read_text(encoding="utf-8", errors="replace")
    source_format = detect_format(raw)
    source = normalize_source(raw, source_format)
    program_match = PROGRAM_ID.search(source)
    suffix = path.suffix.lower()
    kind = "copybook" if suffix in COPYBOOK_EXTENSIONS else "program"
    return CobolUnit(
        path=str(path.relative_to(root)),
        kind=kind,
        source_format=source_format,
        program_id=program_match.group(1).upper() if program_match else None,
        copybooks=sorted({match.upper() for match in COPY.findall(source)}),
        copy_replacing=sorted({match.upper() for match in COPY_REPLACING.findall(source)}),
        calls=sorted({match.upper() for match in CALL.findall(source)}),
        paragraphs=sorted({match.upper() for match in PARAGRAPH.findall(source)}),
        line_count=len(raw.splitlines()),
        byte_count=len(raw.encode("utf-8")),
    )


def scan_tree(root: Path, extensions: set[str] | None = None) -> list[CobolUnit]:
    allowed = extensions or ALL_EXTENSIONS
    return [scan_file(path, root) for path in sorted(root.rglob("*")) if path.suffix.lower() in allowed]


def index_copybooks(roots: list[Path], extensions: set[str] | None = None) -> dict[str, str]:
    """Map an upper-cased copybook name (file stem) to the first file that provides it."""
    allowed = extensions or ALL_EXTENSIONS
    index: dict[str, str] = {}
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() in allowed:
                index.setdefault(path.stem.upper(), str(path))
    return index
