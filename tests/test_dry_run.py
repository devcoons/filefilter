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
    assert result.count("include.extensions:.py") == 2
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
    assert result.hits == {"include.extensions:.py": 0}


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


def test_dry_run_seeds_configured_extension_rules(tmp_path: Path):
    touch(tmp_path / "only.txt")
    cfg = make_config(include_dirs=["**"], include_extensions=["py", "md"])
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)
    assert result.has_rule("include.extensions:.py")
    assert result.has_rule("include.extensions:.md")
    assert result.count("include.extensions:.py") == 0
    assert result.count("include.extensions:.md") == 0
    assert not result.was_hit("include.extensions:.py")


def test_dry_run_extension_pass_skipped_when_hard_excluded(tmp_path: Path):
    touch(tmp_path / "skip.log")
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["py"],
        exclude_extensions=["log"],
    )
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)
    assert result.has_rule("exclude.extensions:.log")
    assert result.count("exclude.extensions:.log") == 1
    assert result.count("include.extensions:.py") == 0


def test_dry_run_extension_pass_skipped_when_out_of_scope(tmp_path: Path):
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "other" / "app.py")
    cfg = make_config(include_dirs=["src/**"], include_extensions=["py"])
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)
    assert result.count("include.extensions:.py") == 1
    assert result.count("include.dirs:src/**") == 1
    assert result.count("include.dirs:**") == 0


def test_dry_run_include_extensions_only_when_pass_applies(tmp_path: Path):
    touch(tmp_path / "readme.md")
    touch(tmp_path / "app.py")
    cfg = make_config(
        include_dirs=["**"],
        include_files=["**/*.md"],
        include_extensions=["py"],
    )
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)
    assert result.count("include.extensions:.py") == 1
    assert str(tmp_path / "readme.md") in result.included
    assert str(tmp_path / "app.py") in result.included


def test_dry_run_has_rule_helper():
    result = DryRunResult(hits={"include.extensions:.py": 0})
    assert result.has_rule("include.extensions:.py")
    assert not result.has_rule("include.extensions:.md")


def test_dry_run_no_include_extensions_configured(tmp_path: Path):
    touch(tmp_path / "app.py")
    cfg = make_config(include_dirs=["**"])
    rules = load(json.dumps(cfg), base=str(tmp_path))
    result = dry_run(rules)
    assert not result.has_rule("include.extensions:.py")
    assert str(tmp_path / "app.py") in result.included
