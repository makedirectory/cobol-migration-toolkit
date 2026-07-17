import json

import jsonschema

from cobol_migrate.cli import run_scan, run_schema
from cobol_migrate.schema import inventory_schema

PROG = """\
       PROGRAM-ID. P.
       DATA DIVISION.
       COPY MISSING.
       PROCEDURE DIVISION.
           CALL "OTHER".
           STOP RUN.
"""


def test_schema_is_valid_draft(tmp_path):
    schema = inventory_schema()
    # the schema itself must be a valid draft 2020-12 schema
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["properties"]["schema_version"]["const"] == 1


def test_real_inventory_validates_against_schema(tmp_path):
    (tmp_path / "P.cbl").write_text(PROG, encoding="utf-8")
    out = tmp_path / "out"
    run_scan(tmp_path, out, [], ["json"], strict=False)
    inventory = json.loads((out / "inventory.json").read_text())
    # a real scan's output must validate against the published schema
    jsonschema.validate(inventory, inventory_schema())


def test_schema_rejects_extra_root_key():
    bad = {
        "schema_version": 1,
        "analyzers": [],
        "units": [],
        "metrics": {},
        "unresolved": {"copybooks": [], "calls": []},
        "reports": {},
        "surprise": True,  # not allowed at the root
    }
    validator = jsonschema.Draft202012Validator(inventory_schema())
    assert not validator.is_valid(bad)


def test_schema_subcommand_writes_file(tmp_path, capsys):
    target = tmp_path / "inventory.schema.json"
    assert run_schema(target) == 0
    written = json.loads(target.read_text())
    assert written["$id"].endswith("inventory.schema.json")


def test_html_has_filter(tmp_path):
    (tmp_path / "P.cbl").write_text(PROG, encoding="utf-8")
    out = tmp_path / "out"
    run_scan(tmp_path, out, [], ["html"], strict=False)
    doc = (out / "report.html").read_text()
    assert 'id="unit-filter"' in doc and 'id="units-table"' in doc
    assert "addEventListener" in doc  # inline filter script present
    assert "http://" not in doc and "https://" not in doc  # still self-contained
