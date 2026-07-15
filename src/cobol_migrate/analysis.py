from __future__ import annotations

from typing import TypedDict

from .scanner import CobolUnit

SCHEMA_VERSION = 1


class Metrics(TypedDict):
    unit_count: int
    program_count: int
    copybook_count: int
    call_edges: int
    copy_edges: int
    unresolved_call_count: int
    unresolved_copybook_count: int
    unreferenced_programs: list[str]
    unreferenced_copybooks: list[str]
    copybooks_using_replacing: list[str]
    max_fan_out: int
    max_fan_in: int


class Unresolved(TypedDict):
    copybooks: list[str]
    calls: list[str]


class Inventory(TypedDict):
    schema_version: int
    units: list[dict[str, object]]
    metrics: Metrics
    unresolved: Unresolved


def build_inventory(units: list[CobolUnit], copybook_index: dict[str, str]) -> Inventory:
    """Aggregate scanned units into the versioned inventory document.

    ``copybook_index`` maps an upper-cased copybook name to a resolving file path
    (see ``scanner.index_copybooks``); names absent from it are reported unresolved.
    """
    programs = [u for u in units if u.kind == "program"]
    copybooks = [u for u in units if u.kind == "copybook"]
    known_programs = {u.program_id for u in units if u.program_id}

    # Call graph: fan-out is what a unit CALLs; fan-in is how often a program is CALLed.
    fan_out: dict[str, int] = {}
    fan_in: dict[str, int] = {pid: 0 for pid in known_programs if pid is not None}
    unresolved_calls: set[str] = set()
    for unit in units:
        source = unit.program_id or unit.path
        fan_out[source] = len(unit.calls)
        for target in unit.calls:
            if target in known_programs:
                fan_in[target] = fan_in.get(target, 0) + 1
            else:
                unresolved_calls.add(target)

    referenced_copybooks: set[str] = set()
    unresolved_copybooks: set[str] = set()
    for unit in units:
        for name in unit.copybooks:
            referenced_copybooks.add(name)
            if name not in copybook_index:
                unresolved_copybooks.add(name)

    unreferenced_programs = sorted(pid for pid, count in fan_in.items() if count == 0)
    unreferenced_copybooks = sorted(
        (u.program_id or _stem(u.path))
        for u in copybooks
        if (u.program_id or _stem(u.path)) not in referenced_copybooks
    )
    uses_replacing = sorted({name for u in units for name in u.copy_replacing})

    metrics: Metrics = {
        "unit_count": len(units),
        "program_count": len(programs),
        "copybook_count": len(copybooks),
        "call_edges": sum(fan_out.values()),
        "copy_edges": sum(len(u.copybooks) for u in units),
        "unresolved_call_count": len(unresolved_calls),
        "unresolved_copybook_count": len(unresolved_copybooks),
        "unreferenced_programs": unreferenced_programs,
        "unreferenced_copybooks": unreferenced_copybooks,
        "copybooks_using_replacing": uses_replacing,
        "max_fan_out": max(fan_out.values(), default=0),
        "max_fan_in": max(fan_in.values(), default=0),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "units": [unit.to_dict() for unit in units],
        "metrics": metrics,
        "unresolved": {
            "copybooks": sorted(unresolved_copybooks),
            "calls": sorted(unresolved_calls),
        },
    }


def _stem(path: str) -> str:
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[0].upper()
