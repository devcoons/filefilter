from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from filefilter import Ruleset, load


def test_ruleset_resolves_relative_root_against_base(tmp_path: Path):
    sub = tmp_path / "project"
    sub.mkdir()
    cfg = {"root_dir": ".", "filters": {"include": {}, "exclude": {}}}
    rules = load(json.dumps(cfg), base=str(sub))
    assert rules.root_dir == os.path.normpath(str(sub))


def test_ruleset_empty_resolve_base_uses_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"root_dir": ".", "filters": {"include": {}, "exclude": {}}}
    rules = Ruleset(cfg, resolve_base="")
    assert rules.root_dir == os.path.normpath(str(tmp_path))


def test_ruleset_resolves_absolute_root(tmp_path: Path):
    cfg = {"root_dir": str(tmp_path), "filters": {"include": {}, "exclude": {}}}
    rules = load(json.dumps(cfg), base="/should/not/matter")
    assert rules.root_dir == os.path.normpath(str(tmp_path))


def test_ruleset_script_resolve_base():
    cfg = {"root_dir": ".", "filters": {"include": {}, "exclude": {}}}
    rules = Ruleset(cfg, resolve_base="script")
    expected = os.path.normpath(os.path.dirname(os.path.abspath(__file__)).replace("tests", "src/filefilter"))
    # resolve_base=script points at the package directory, not tests/
    from filefilter import ruleset as ruleset_module

    assert rules.root_dir == os.path.normpath(os.path.dirname(os.path.abspath(ruleset_module.__file__)))


def test_parse_extensions_normalizes_values():
    cfg = {
        "root_dir": ".",
        "filters": {
            "include": {"extensions": ["PY", ".MD", "tar.gz", ".*", ""]},
            "exclude": {"extensions": [".log"]},
        },
    }
    rules = Ruleset(cfg, resolve_base=".")
    assert rules.inc_exts == [".py", ".md", ".tar.gz", ".*"]
    assert rules.exc_exts == [".log"]


def test_empty_dir_patterns_are_ignored(tmp_path: Path):
    cfg = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": ["/", "", "  "], "extensions": [".*"]},
            "exclude": {"dirs": ["/"]},
        },
    }
    (tmp_path / "file.txt").write_text("")
    rules = load(json.dumps(cfg), base=str(tmp_path))
    from filefilter import scan

    paths = scan(rules)
    assert paths == [os.path.normpath(str(tmp_path / "file.txt"))]
