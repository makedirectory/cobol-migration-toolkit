from pathlib import Path

from cobol_migrate.scanner import scan_tree


def test_scan_example() -> None:
    root = Path(__file__).parents[1] / "examples"
    units = scan_tree(root)
    customer = next(unit for unit in units if unit.program_id == "CUSTOMER")
    assert "CUSTOMER-RECORD" in customer.copybooks
    assert "VALIDATE-CUSTOMER" in customer.calls
