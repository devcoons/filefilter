from __future__ import annotations

import json
from pathlib import Path

from filefilter import DryRunResult, dry_run, load, scan
from conftest import make_config, norm_paths, touch


def test_dry_run_per_rule_hit_counts(tmp_path: Path):
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "src" / "test_foo.py")
    touch(tmp_path / "src" / "test_keep.py")
    touch(tmp_path / "build" / "out.py")
    touch(tmp_path / "notes.txt")

    cfg = make_config(
        include_dirs=["**"],
        include_ofiles=["**/test_keep.py"],
        include_extensions=["py"],
        exclude_dirs=["**/build/**"],
        exclude_files=["**/test_*.py"],
    )
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)

    assert result.scanned == 5
    assert result.excluded == 3
    assert len(result.included) == 2
    assert result.was_hit("include.dirs:**")
    assert result.count("include.dirs:**") == 5
    assert result.count("include.extensions:.py") == 4
    assert result.count("exclude.dirs:**/build/**") == 1
    assert result.count("exclude.files:**/test_*.py") == 2
    assert result.count("include.ofiles:**/test_keep.py") == 1
    assert not result.was_hit("include.files:readme.md")
    assert result.count("exclude.extensions:.log") == 0

    included = set(norm_paths(result.included))
    assert included == set(norm_paths(scan(rules)))


def test_dry_run_empty_tree(tmp_path: Path):
    cfg = make_config(include_dirs=["**"], include_extensions=["py"])
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)
    assert result.scanned == 0
    assert result.included == []
    assert result.hits == {}


def test_dry_run_skips_symlinks(tmp_path: Path):
    touch(tmp_path / "real.py")
    link = tmp_path / "linked.py"
    link.symlink_to(tmp_path / "real.py")
    cfg = make_config(include_dirs=["**"], include_extensions=["py"])
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)
    assert result.scanned == 1
    assert result.count("include.dirs:**") == 1


def test_dry_run_result_helpers():
    result = DryRunResult(scanned=10, included=["a", "b"], hits={"include.dirs:**": 7})
    assert result.excluded == 8
    assert result.count("missing") == 0
    assert not result.was_hit("missing")
    assert result.was_hit("include.dirs:**")
    assert result.count("include.dirs:**") == 7
