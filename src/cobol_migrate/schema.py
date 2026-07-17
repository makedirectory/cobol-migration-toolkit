"""JSON Schema for `inventory.json` — the stable contract downstream tools (incl. Cartograph) consume.

Kept in sync with `analysis.Inventory` / `scanner.CobolUnit`. Emitted via `cobol-migrate schema`.
Additive fields are allowed (units and reports permit extra properties) so paid plugins can extend
the output without breaking validation; breaking changes bump `SCHEMA_VERSION`.
"""

from __future__ import annotations

from .analysis import SCHEMA_VERSION

SCHEMA_ID = "https://makedirectory.github.io/cobol-migration-toolkit/inventory.schema.json"

_STR_ARRAY = {"type": "array", "items": {"type": "string"}}


def inventory_schema() -> dict[str, object]:
    """Return the JSON Schema (draft 2020-12) describing `inventory.json`."""
    unit = {
        "type": "object",
        "required": [
            "path",
            "kind",
            "source_format",
            "program_id",
            "copybooks",
            "copy_replacing",
            "calls",
            "paragraphs",
            "line_count",
            "byte_count",
        ],
        "properties": {
            "path": {"type": "string"},
            "kind": {"enum": ["program", "copybook"]},
            "source_format": {"enum": ["fixed", "free"]},
            "program_id": {"type": ["string", "null"]},
            "copybooks": _STR_ARRAY,
            "copy_replacing": _STR_ARRAY,
            "calls": _STR_ARRAY,
            "paragraphs": _STR_ARRAY,
            "line_count": {"type": "integer", "minimum": 0},
            "byte_count": {"type": "integer", "minimum": 0},
            # Per-unit analyzer output (optional): { "<analyzer>": { ... } }
            "analyses": {"type": "object", "additionalProperties": {"type": "object"}},
        },
        # Allow additional fields so plugins can extend a unit entry.
        "additionalProperties": True,
    }

    metrics = {
        "type": "object",
        "properties": {
            "unit_count": {"type": "integer"},
            "program_count": {"type": "integer"},
            "copybook_count": {"type": "integer"},
            "call_edges": {"type": "integer"},
            "copy_edges": {"type": "integer"},
            "unresolved_call_count": {"type": "integer"},
            "unresolved_copybook_count": {"type": "integer"},
            "unreferenced_programs": _STR_ARRAY,
            "unreferenced_copybooks": _STR_ARRAY,
            "copybooks_using_replacing": _STR_ARRAY,
            "max_fan_out": {"type": "integer"},
            "max_fan_in": {"type": "integer"},
        },
        "additionalProperties": True,
    }

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "COBOL Migration Toolkit inventory",
        "type": "object",
        "required": ["schema_version", "analyzers", "units", "metrics", "unresolved", "reports"],
        "properties": {
            "schema_version": {"type": "integer", "const": SCHEMA_VERSION},
            "analyzers": _STR_ARRAY,
            "units": {"type": "array", "items": unit},
            "metrics": metrics,
            "unresolved": {
                "type": "object",
                "required": ["copybooks", "calls"],
                "properties": {"copybooks": _STR_ARRAY, "calls": _STR_ARRAY},
                "additionalProperties": False,
            },
            # Estate-level inventory-analyzer output: { "<analyzer>": { ... } }
            "reports": {"type": "object", "additionalProperties": {"type": "object"}},
        },
        "additionalProperties": False,
    }
