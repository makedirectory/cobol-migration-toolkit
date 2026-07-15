import argparse
from pathlib import Path

from cobol_migrate.cli import build_parser, merge_config
from cobol_migrate.config import find_config, load_config

CONFIG = """\
copybook_paths = ["copybooks"]
format = ["json", "html"]
strict = true
analyzers = ["complexity"]
extensions = ["cbl", ".CPY"]
output = "out"
dialect = "ibm"
"""


def _args(argv: list[str]) -> argparse.Namespace:
    return build_parser().parse_args(["scan", *argv])


def test_load_config_parses_and_normalizes(tmp_path):
    cfg_path = tmp_path / ".cobolmigrate.toml"
    cfg_path.write_text(CONFIG, encoding="utf-8")
    cfg = load_config(cfg_path)
    assert cfg.copybook_paths == ["copybooks"]
    assert cfg.formats == ["json", "html"]
    assert cfg.strict is True
    assert cfg.analyzers == ["complexity"]
    assert cfg.extensions == {".cbl", ".cpy"}  # normalized: leading dot + lowercase
    assert cfg.output == "out"
    assert cfg.options == {"dialect": "ibm"}  # unknown keys pass through


def test_find_config_autodiscovers_in_source(tmp_path):
    (tmp_path / ".cobolmigrate.toml").write_text("strict = true\n", encoding="utf-8")
    assert find_config(tmp_path, None) == tmp_path / ".cobolmigrate.toml"
    assert find_config(tmp_path, None) is not None
    # explicit path wins
    explicit = tmp_path / "custom.toml"
    explicit.write_text("", encoding="utf-8")
    assert find_config(tmp_path, explicit) == explicit


def test_config_supplies_defaults(tmp_path):
    cfg_path = tmp_path / ".cobolmigrate.toml"
    cfg_path.write_text(CONFIG, encoding="utf-8")
    cfg = load_config(cfg_path)
    resolved = merge_config(_args(["src"]), cfg)
    assert resolved.formats == ["json", "html"]
    assert resolved.strict is True
    assert resolved.analyzers == ["complexity"]
    assert resolved.output == Path("out")
    assert resolved.extensions == {".cbl", ".cpy"}
    assert resolved.options == {"dialect": "ibm"}
    # config copybook_paths resolved relative to the config file's directory
    assert (tmp_path / "copybooks").resolve() in resolved.copybook_paths


def test_cli_overrides_config(tmp_path):
    cfg_path = tmp_path / ".cobolmigrate.toml"
    cfg_path.write_text(CONFIG, encoding="utf-8")
    cfg = load_config(cfg_path)
    resolved = merge_config(_args(["src", "--format", "md", "--output", "build2"]), cfg)
    assert resolved.formats == ["md"]  # CLI format wins
    assert resolved.output == Path("build2")  # CLI output wins
    assert resolved.strict is True  # not overridden → from config


def test_no_config_uses_builtin_defaults():
    cfg = load_config(None)
    resolved = merge_config(_args(["src"]), cfg)
    assert resolved.formats == ["json", "md", "dot", "html"]
    assert resolved.strict is False
    assert resolved.output == Path("build")
    assert resolved.extensions is None
