"""Several filters are applied separately; a file is kept if any of them selects it."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from filefilter import dry_run, load, matches, scan, select
from conftest import touch


def _spec(include, exclude=None):
    return {"include": include, "exclude": exclude or {}}


PY_EXCEPT_SKIP = _spec(
    {"dirs": ["**"], "files": [], "extensions": ["py"]},
    {"dirs": ["**/skip/**"], "files": [], "extensions": []},
)
KEEP_ONLY = _spec(
    {"dirs": [], "files": ["**/skip/keep.py"], "extensions": []},
    {"dirs": [], "files": [], "extensions": []},
)


def _cfg(filters):
    return {"root_dir": ".", "filters": filters}


def _tree(tmp_path: Path) -> None:
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "docs" / "guide.md")
    touch(tmp_path / "skip" / "other.py")
    touch(tmp_path / "skip" / "keep.py")


def test_one_element_list_matches_a_single_object(tmp_path: Path):
    _tree(tmp_path)
    as_object = _cfg(PY_EXCEPT_SKIP)
    as_list = _cfg([PY_EXCEPT_SKIP])
    assert select(json.dumps(as_list), base=str(tmp_path)) == select(
        json.dumps(as_object), base=str(tmp_path)
    )
    object_rules = load(json.dumps(as_object), base=str(tmp_path))
    list_rules = load(json.dumps(as_list), base=str(tmp_path))
    assert list_rules.inc_dirs == object_rules.inc_dirs == ["**"]
    assert list_rules.exc_dirs == ["**/skip/**"]
    assert dry_run(list_rules).hits == dry_run(object_rules).hits
    assert "include.dirs:**" in dry_run(list_rules).hits


def test_filters_are_unioned_not_merged(tmp_path: Path):
    _tree(tmp_path)
    combined = _cfg([PY_EXCEPT_SKIP, KEEP_ONLY])
    only_py = set(select(json.dumps(_cfg(PY_EXCEPT_SKIP)), base=str(tmp_path)))
    only_keep = set(select(json.dumps(_cfg(KEEP_ONLY)), base=str(tmp_path)))
    selected = select(json.dumps(combined), base=str(tmp_path))

    assert set(selected) == only_py | only_keep
    assert len(selected) == len(set(selected))
    assert str(tmp_path / "src" / "app.py") in selected
    assert str(tmp_path / "skip" / "keep.py") in selected
    assert str(tmp_path / "skip" / "other.py") not in selected
    assert str(tmp_path / "docs" / "guide.md") not in selected
    assert str(tmp_path / "skip" / "keep.py") not in only_py

    rules = load(json.dumps(combined), base=str(tmp_path))
    assert len(rules.filters) == 2
    assert rules.filters[0].inc_exts == [".py"]
    assert rules.filters[1].include_files == ["**/skip/keep.py"]
    assert matches(str(tmp_path / "skip" / "keep.py"), rules) is True
    assert matches(str(tmp_path / "docs" / "guide.md"), rules) is False
    assert set(dry_run(rules).included) == set(scan(rules))


def test_repeated_filters_do_not_duplicate_paths(tmp_path: Path):
    _tree(tmp_path)
    rules = load(json.dumps(_cfg([PY_EXCEPT_SKIP, PY_EXCEPT_SKIP, PY_EXCEPT_SKIP])), base=str(tmp_path))
    selected = scan(rules)
    assert selected == scan(load(json.dumps(_cfg(PY_EXCEPT_SKIP)), base=str(tmp_path)))
    report = dry_run(rules)
    assert report.count("filters[0].include.dirs:**") == report.scanned
    assert report.count("filters[2].include.dirs:**") == report.scanned
    assert report.has_rule("filters[0].include.extensions:.py")
    assert "include.dirs:**" not in report.hits


def test_yaml_and_toml_lists_match_json(tmp_path: Path):
    _tree(tmp_path)
    json_text = json.dumps(_cfg([PY_EXCEPT_SKIP, KEEP_ONLY]))
    yaml_text = """\
root_dir: "."
filters:
  - include:
      dirs: ["**"]
      files: []
      extensions: ["py"]
    exclude:
      dirs: ["**/skip/**"]
      files: []
      extensions: []
  - include:
      dirs: []
      files: ["**/skip/keep.py"]
      extensions: []
    exclude:
      dirs: []
      files: []
      extensions: []
"""
    toml_text = """\
root_dir = "."

[[filters]]
[filters.include]
dirs = ["**"]
files = []
extensions = ["py"]
[filters.exclude]
dirs = ["**/skip/**"]
files = []
extensions = []

[[filters]]
[filters.include]
dirs = []
files = ["**/skip/keep.py"]
extensions = []
[filters.exclude]
dirs = []
files = []
extensions = []
"""
    expected = select(json_text, base=str(tmp_path))
    assert select(yaml_text, base=str(tmp_path)) == expected
    assert select(toml_text, base=str(tmp_path)) == expected


def test_readme_multi_filter_samples(tmp_path: Path):
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    start = readme.index("### Multiple filters")
    body = readme[start:readme.index("##  Pattern Rules Recap")]
    _tree(tmp_path)
    expected = {
        str(tmp_path / "src" / "app.py"),
        str(tmp_path / "skip" / "keep.py"),
    }
    for lang in ("json", "yaml", "toml"):
        marker = f"```{lang}\n"
        chunk = body[body.index(marker) + len(marker):]
        sample = chunk[:chunk.index("```")]
        assert set(select(sample, base=str(tmp_path))) == expected


def test_invalid_filters_are_rejected():
    with pytest.raises(ValueError, match="at least one"):
        load('{"root_dir": ".", "filters": []}')
    with pytest.raises(ValueError, match="mapping or a list"):
        load('{"root_dir": ".", "filters": "py"}')
    with pytest.raises(ValueError, match="each filter"):
        load('{"root_dir": ".", "filters": [1]}')
    with pytest.raises(KeyError):
        load('{"root_dir": ".", "filters": [{"include": {}}]}')
    with pytest.raises(KeyError):
        load('{"root_dir": ".", "filters": {"include": {}}}')


def test_original_json_object_matches_one_element_array(tmp_path: Path):
    """Call style from the previous version: a JSON object passed to load and select."""
    touch(tmp_path / "main.py")
    touch(tmp_path / "docs" / "readme.md")
    touch(tmp_path / "__pycache__" / "main.py")
    cfg_json = """{
        "root_dir": ".",
        "filters": {
            "include": { "dirs": ["**"], "files": [], "extensions": ["py"] },
            "exclude": { "dirs": ["__pycache__"], "files": [], "extensions": [] }
        }
    }"""
    cfg_list = """{
        "root_dir": ".",
        "filters": [{
            "include": { "dirs": ["**"], "files": [], "extensions": ["py"] },
            "exclude": { "dirs": ["__pycache__"], "files": [], "extensions": [] }
        }]
    }"""
    rules = load(cfg_json, base=str(tmp_path))
    selected = select(cfg_json, base=str(tmp_path))
    assert selected == select(cfg_list, base=str(tmp_path))
    assert selected == scan(rules)
    assert matches(str(tmp_path / "main.py"), rules) is True
    assert matches(str(tmp_path / "__pycache__" / "main.py"), rules) is False
    assert dry_run(rules).count("include.dirs:**") == dry_run(rules).scanned
    assert select(config_json=cfg_list, base=str(tmp_path)) == selected


def test_hard_exclude_in_one_filter_does_not_block_another(tmp_path: Path):
    touch(tmp_path / "app.py")
    touch(tmp_path / "debug.log")
    rules = load(json.dumps(_cfg([
        _spec(
            {"dirs": ["**"], "extensions": ["py"]},
            {"extensions": ["log"]},
        ),
        _spec({"files": ["**/*.log"]}),
    ])), base=str(tmp_path))
    selected = set(scan(rules))
    assert str(tmp_path / "app.py") in selected
    assert str(tmp_path / "debug.log") in selected


def test_odirs_do_not_leak_into_another_filter(tmp_path: Path):
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "skip" / "other.py")
    touch(tmp_path / "skip" / "note.md")
    py_except_skip = _spec(
        {"dirs": ["**"], "extensions": ["py"]},
        {"dirs": ["**/skip/**"]},
    )
    md_with_unrelated_odirs = _spec(
        {"dirs": ["**"], "odirs": ["**/skip/**"], "extensions": ["md"]},
    )
    rules = load(json.dumps(_cfg([py_except_skip, md_with_unrelated_odirs])), base=str(tmp_path))
    selected = set(scan(rules))
    assert str(tmp_path / "src" / "app.py") in selected
    assert str(tmp_path / "skip" / "note.md") in selected
    assert str(tmp_path / "skip" / "other.py") not in selected


def test_ofiles_override_only_their_own_filter(tmp_path: Path):
    touch(tmp_path / "app.py")
    touch(tmp_path / "test_keep.py")
    touch(tmp_path / "test_foo.py")
    drop_tests = _spec(
        {"dirs": ["**"], "extensions": ["py"]},
        {"files": ["**/test_*.py"]},
    )
    keep_inside_second = _spec(
        {"dirs": ["**"], "ofiles": ["**/test_keep.py"], "extensions": ["py"]},
        {"files": ["**/test_*.py"]},
    )
    rules = load(json.dumps(_cfg([drop_tests, keep_inside_second])), base=str(tmp_path))
    selected = set(scan(rules))
    assert str(tmp_path / "app.py") in selected
    assert str(tmp_path / "test_keep.py") in selected
    assert str(tmp_path / "test_foo.py") not in selected


def test_empty_filter_in_an_array_includes_every_file(tmp_path: Path):
    touch(tmp_path / "app.py")
    touch(tmp_path / "notes.md")
    only_py = _spec({"dirs": ["**"], "extensions": ["py"]})
    accept_all = _spec({})
    rules = load(json.dumps(_cfg([only_py, accept_all])), base=str(tmp_path))
    assert set(scan(rules)) == {
        str(tmp_path / "app.py"),
        str(tmp_path / "notes.md"),
    }


def test_overlapping_filters_keep_walk_order_and_dry_run_counts(tmp_path: Path):
    _tree(tmp_path)
    rules = load(json.dumps(_cfg([PY_EXCEPT_SKIP, KEEP_ONLY])), base=str(tmp_path))
    selected = select(json.dumps(_cfg([PY_EXCEPT_SKIP, KEEP_ONLY])), base=str(tmp_path))
    assert selected == scan(rules)
    assert len(selected) == len(set(selected))

    report = dry_run(rules)
    assert report.included == selected
    assert report.scanned == 4
    assert report.excluded == 2
    assert report.count("filters[0].exclude.dirs:**/skip/**") == 2
    assert report.count("filters[1].include.files:**/skip/keep.py") == 1
    assert report.has_rule("filters[0].include.extensions:.py")
    assert str(tmp_path / "skip" / "keep.py") in report.included


def test_array_config_file_matches_its_text(tmp_path: Path):
    scanned = tmp_path / "proj"
    for rel in ("src/app.py", "docs/guide.md", "skip/other.py", "skip/keep.py"):
        touch(scanned / rel)
    payload = json.dumps(_cfg([PY_EXCEPT_SKIP, KEEP_ONLY]))
    cfg_path = tmp_path / "filters.json"
    cfg_path.write_text(payload, encoding="utf-8")
    assert select(cfg_path, base=str(scanned)) == select(payload, base=str(scanned))


def test_multi_filter_patterns_are_case_insensitive(tmp_path: Path):
    touch(tmp_path / "SRC" / "App.PY")
    rules = load(json.dumps(_cfg([
        _spec({"dirs": ["src/**"], "extensions": ["PY"]}),
    ])), base=str(tmp_path))
    assert scan(rules) == [str(tmp_path / "SRC" / "App.PY")]


def test_multi_filter_ignores_symlinks(tmp_path: Path):
    touch(tmp_path / "real.py")
    (tmp_path / "linked.py").symlink_to(tmp_path / "real.py")
    rules = load(json.dumps(_cfg([
        _spec({"dirs": ["**"], "extensions": ["py"]}),
        _spec({"files": ["**/*"]}),
    ])), base=str(tmp_path))
    assert scan(rules) == [str(tmp_path / "real.py")]
    assert dry_run(rules).scanned == 1
