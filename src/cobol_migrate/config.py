"""`.cobolmigrate.toml` project configuration.

Lets teams keep scan settings in a file instead of long command lines. CLI flags take
precedence over the config file; the file provides defaults. Unknown top-level keys (e.g.
``dialect``) are passed through to analyzers via ``ScanContext.options``.

Example ``.cobolmigrate.toml``::

    copybook_paths = ["copybooks", "shared/cpy"]
    format = ["json", "html"]
    strict = true
    analyzers = ["all"]
    extensions = [".cbl", ".cob", ".cpy"]
    output = "build"
    dialect = "ibm"            # passed through to analyzers
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = ".cobolmigrate.toml"

_KNOWN_KEYS = {"copybook_paths", "format", "strict", "analyzers", "extensions", "output"}


@dataclass
class Config:
    copybook_paths: list[str] = field(default_factory=list)
    formats: list[str] | None = None
    strict: bool = False
    analyzers: list[str] | None = None
    extensions: set[str] | None = None
    output: str | None = None
    options: dict[str, object] = field(default_factory=dict)
    path: Path | None = None


def find_config(source: Path, explicit: Path | None) -> Path | None:
    """Return the config path: the explicit one, else an auto-discovered file."""
    if explicit is not None:
        return explicit
    for candidate in (source / CONFIG_FILENAME, Path.cwd() / CONFIG_FILENAME):
        if candidate.is_file():
            return candidate
    return None


def _normalize_extensions(values: list[object]) -> set[str]:
    result: set[str] = set()
    for value in values:
        ext = str(value).lower()
        result.add(ext if ext.startswith(".") else f".{ext}")
    return result


def load_config(path: Path | None) -> Config:
    if path is None:
        return Config()
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return Config(
        copybook_paths=[str(p) for p in data.get("copybook_paths", [])],
        formats=[str(f) for f in data["format"]] if "format" in data else None,
        strict=bool(data.get("strict", False)),
        analyzers=[str(a) for a in data["analyzers"]] if "analyzers" in data else None,
        extensions=_normalize_extensions(data["extensions"]) if "extensions" in data else None,
        output=str(data["output"]) if "output" in data else None,
        options={k: v for k, v in data.items() if k not in _KNOWN_KEYS},
        path=path,
    )
