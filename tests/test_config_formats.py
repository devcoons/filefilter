"""JSON, YAML, and TOML configuration must load through load() and select()."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from filefilter import dry_run, load, scan, select

CFG = {
    "root_dir": ".",
    "filters": {
        "include": {
            "dirs": ["src/**", "**/01/**", "*/pkg"],
            "odirs": ["**/keep/**"],
            "ofiles": ["**/test_keep.py"],
            "files": ["*.py", "Makefile"],
            "extensions": ["py", "tar.gz"],
        },
        "exclude": {
            "dirs": ["**/build/**"],
            "files": ["**/hello.py"],
            "extensions": ["log"],
        },
    },
}

YAML_TEXT = """\
root_dir: "."
filters:
  include:
    dirs: ["src/**", "**/01/**", "*/pkg"]
    odirs: ["**/keep/**"]
    ofiles: ["**/test_keep.py"]
    files: ["*.py", "Makefile"]
    extensions: ["py", "tar.gz"]
  exclude:
    dirs: ["**/build/**"]
    files: ["**/hello.py"]
    extensions: ["log"]
"""

TOML_TEXT = """\
# equivalent rules
root_dir = "."

[filters.include]
dirs = ["src/**", "**/01/**", "*/pkg"]
odirs = ["**/keep/**"]
ofiles = ["**/test_keep.py"]
files = ["*.py", "Makefile"]
extensions = ["py", "tar.gz"]

[filters.exclude]
dirs = ["**/build/**"]
files = ["**/hello.py"]
extensions = ["log"]
"""

JSON_TEXT = json.dumps(CFG)


def _fields(rules):
    return {
        "root": rules.root_dir,
        "inc_dirs": rules.inc_dirs,
        "inc_odirs": rules.inc_odirs,
        "exc_dirs": rules.exc_dirs,
        "include_files": rules.include_files,
        "include_ofiles": rules.include_ofiles,
        "exclude_files": rules.exclude_files,
        "inc_exts": rules.inc_exts,
        "exc_exts": rules.exc_exts,
    }


def test_yaml_and_toml_match_json_rules_and_selection(tree: Path):
    json_rules = load(JSON_TEXT, base=str(tree))
    yaml_rules = load(YAML_TEXT, base=str(tree))
    toml_rules = load(TOML_TEXT, base=str(tree))

    assert _fields(yaml_rules) == _fields(json_rules)
    assert _fields(toml_rules) == _fields(json_rules)

    json_selected = select(JSON_TEXT, base=str(tree))
    assert select(YAML_TEXT, base=str(tree)) == json_selected
    assert select(TOML_TEXT, base=str(tree)) == json_selected
    assert scan(yaml_rules) == json_selected

    json_report = dry_run(json_rules)
    yaml_report = dry_run(yaml_rules)
    toml_report = dry_run(toml_rules)
    assert yaml_report.hits == json_report.hits
    assert toml_report.hits == json_report.hits
    assert yaml_report.included == json_report.included
    assert toml_report.included == json_report.included


def test_config_file_paths_match_json(tree: Path, tmp_path: Path):
    files = {
        "rules.json": JSON_TEXT,
        "rules.yaml": YAML_TEXT,
        "rules.yml": YAML_TEXT,
        "rules.toml": TOML_TEXT,
        "RULES.YAML": YAML_TEXT,
    }
    expected = select(JSON_TEXT, base=str(tree))
    for name, body in files.items():
        path = tmp_path / name
        path.write_text(body, encoding="utf-8")
        assert select(str(path), base=str(tree)) == expected
        assert select(path, base=str(tree)) == expected
        assert _fields(load(path, base=str(tree))) == _fields(load(JSON_TEXT, base=str(tree)))


def test_relative_config_path_uses_cwd(tree: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "filters.toml").write_text(TOML_TEXT, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert select("filters.toml", base=str(tree)) == select(JSON_TEXT, base=str(tree))


def test_config_json_keyword_is_an_alias(tree: Path):
    positional = load(JSON_TEXT, base=str(tree))
    assert _fields(load(config_json=YAML_TEXT, base=str(tree))) == _fields(positional)
    assert select(config_json=TOML_TEXT, base=str(tree)) == select(JSON_TEXT, base=str(tree))


def test_load_and_select_reject_bad_arguments():
    with pytest.raises(TypeError, match="both"):
        load(JSON_TEXT, config_json=JSON_TEXT)
    with pytest.raises(TypeError, match="both"):
        select(YAML_TEXT, config_json=YAML_TEXT)
    with pytest.raises(TypeError, match="missing required argument"):
        load()
    with pytest.raises(TypeError, match="missing required argument"):
        select(base="cwd")
    with pytest.raises(TypeError, match="config must be"):
        load(123)


def test_yaml_plain_scalars_stay_strings_and_match(tmp_path: Path):
    for name in ("on", "01", "yes", "null"):
        path = tmp_path / name / "a.py"
        path.parent.mkdir(parents=True)
        path.write_text("")
    (tmp_path / "no" / "skip.py").parent.mkdir()
    (tmp_path / "no" / "skip.py").write_text("")

    rules = load(
        """\
root_dir: "."
filters:
  include:
    dirs: [on, 01, yes, null]
    extensions: [py]
  exclude:
    dirs: [no]
    files: []
    extensions: []
""",
        base=str(tmp_path),
    )
    assert rules.inc_dirs == ["on", "01", "yes", "null"]
    assert rules.exc_dirs == ["no"]
    selected = set(scan(rules))
    for name in ("on", "01", "yes", "null"):
        assert str(tmp_path / name / "a.py") in selected
    assert str(tmp_path / "no" / "skip.py") not in selected


def test_flow_yaml_and_document_markers_load(tmp_path: Path):
    (tmp_path / "a.py").write_text("")
    flow = '{root_dir: ".", filters: {include: {extensions: [py]}, exclude: {}}}'
    marked = """\
---
# comment
root_dir: "."
filters:
  include:
    extensions: [py]
  exclude: {}
...
"""
    assert scan(load(flow, base=str(tmp_path))) == [str(tmp_path / "a.py")]
    assert scan(load(marked, base=str(tmp_path))) == [str(tmp_path / "a.py")]


def test_bom_json_text_and_utf8_sig_file(tree: Path, tmp_path: Path):
    expected = _fields(load(JSON_TEXT, base=str(tree)))
    assert _fields(load("\ufeff" + JSON_TEXT, base=str(tree))) == expected
    path = tmp_path / "bom.json"
    path.write_bytes(b"\xef\xbb\xbf" + JSON_TEXT.encode("utf-8"))
    assert _fields(load(path, base=str(tree))) == expected


def test_single_line_json_is_not_treated_as_a_path(tree: Path):
    assert _fields(load(json.dumps(CFG), base=str(tree))) == _fields(load(JSON_TEXT, base=str(tree)))


def test_inline_text_ending_with_a_config_suffix_is_parsed(tmp_path: Path):
    (tmp_path / "a.py").write_text("")
    text = """\
root_dir: "."
filters:
  include:
    extensions: [py]
  exclude: {}
"""
    # One line, ends with a config suffix, but it is a document rather than a path.
    with pytest.raises(KeyError):
        load("root_dir: filters.yaml")
    assert scan(load(text, base=str(tmp_path))) == [str(tmp_path / "a.py")]


def test_missing_config_file_and_directory(tmp_path: Path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load(str(missing))
    directory = tmp_path / "cfg.toml"
    directory.mkdir()
    with pytest.raises(IsADirectoryError):
        load(directory)


@pytest.mark.parametrize(
    "name,body,exc",
    [
        ("bad.json", "{", json.JSONDecodeError),
        ("empty.json", "   \n", ValueError),
        ("list.json", "[]", ValueError),
        ("bad.yaml", ":\n  -", ValueError),
        ("empty.yml", "\n\n", ValueError),
        ("list.yaml", "- a\n- b\n", ValueError),
        ("scalar.yaml", "hello\n", ValueError),
        ("bad.toml", "=\n", ValueError),
        ("empty.toml", "  \n", ValueError),
    ],
)
def test_explicit_format_errors(tmp_path: Path, name: str, body: str, exc):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    with pytest.raises(exc):
        load(path)


def test_autodetect_errors():
    with pytest.raises(json.JSONDecodeError):
        load("{")
    with pytest.raises(ValueError, match="empty"):
        load("   \n\t")
    with pytest.raises(ValueError, match="must be a mapping"):
        load("[]")
    with pytest.raises(ValueError, match="could not parse"):
        load("hello")
    with pytest.raises(ValueError, match="empty"):
        load("# only a comment\n")
    with pytest.raises(ValueError, match="could not parse"):
        load("root_dir: [\n")
    with pytest.raises(KeyError):
        load('[[tools]]\nname = "filefilter"\n')


def _fence(text: str, lang: str) -> str:
    marker = f"```{lang}\n"
    start = text.index(marker) + len(marker)
    return text[start:text.index("```", start)]


def test_readme_yaml_and_toml_samples(tmp_path: Path):
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    readme = readme[readme.index("##  Configuration formats"):]
    (tmp_path / "main.py").write_text("")
    (tmp_path / "docs" / "readme.md").parent.mkdir()
    (tmp_path / "docs" / "readme.md").write_text("")
    (tmp_path / "__pycache__" / "main.py").parent.mkdir()
    (tmp_path / "__pycache__" / "main.py").write_text("")

    expected = {
        str(tmp_path / "main.py"),
    }
    for lang in ("yaml", "toml"):
        selected = set(select(_fence(readme, lang), base=str(tmp_path)))
        assert selected == expected


def test_toml_table_header_and_invalid_toml_value():
    with pytest.raises(KeyError):
        load("[filters.include]\ndirs = ['**']\n")
    with pytest.raises(ValueError, match="could not parse"):
        load('foo = bar\n')
