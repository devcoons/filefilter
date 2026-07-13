from __future__ import annotations

import json
from pathlib import Path

import pytest

from filefilter import filter_paths, match_dir, match_file

from conftest import make_config, norm_paths, select_paths, touch, tree  # noqa: F401


def test_filter_paths_basic_semantics(tree: Path):
    cfg = make_config(
        include_dirs=["**/01/**"],
        include_files=["report_*"],
        include_extensions=[".*"],
        exclude_extensions=[".ext2"],
    )
    got = norm_paths(filter_paths(json.dumps(cfg), resolve_base=str(tree)))
    expect = norm_paths(
        [
            str(tree / "report_2025.csv"),
            str(tree / "A" / "01" / "x.txt"),
            str(tree / "B" / "01" / "03" / "z.txt"),
        ]
    )
    assert got == expect


@pytest.mark.parametrize(
    "fname,patterns,expected",
    [
        ("report_", ["report_*"], False),
        ("report_", ["report_**"], True),
        ("x/file.txt", ["file.txt"], False),
        ("file.txt", ["file.txt"], True),
        ("x/file.txt", ["*/file.txt"], True),
        ("x/y/file.txt", ["*/*/file.txt"], True),
        ("x/y/file.txt", ["**/file.txt"], True),
        ("src/app.py", ["*.py"], False),
        ("main.py", ["*.py"], True),
        ("src/app.py", ["**/*.py"], True),
        ("deep/x/y/file.py", ["**/file**.py"], True),
        ("deep/x/y/fileA.py", ["**/file*.py"], True),
        ("deep/x/y/file.py", ["**/file*.py"], False),
        ("pkg/LICENSE", ["LICENSE*"], False),
        ("pkg/LICENSE-MIT", ["**/LICENSE*"], True),
        ("pkg/LICENSE", ["**/LICENSE**"], True),
        ("README.md", ["README.*"], True),
        ("README", ["README.*"], False),
        ("README", ["README.**"], True),
    ],
)
def test_file_location_and_star_semantics(
    tmp_path: Path, fname: str, patterns: list[str], expected: bool
):
    target = touch(tmp_path / fname)
    cfg = make_config(include_files=patterns, include_extensions=[".*"])
    paths = select_paths(tmp_path, cfg)
    assert (str(target) in paths) is expected


def test_dir_root_one_any_semantics(tree: Path):
    cfg_root = make_config(include_dirs=["Folder"], include_extensions=[".*"])
    got_root = select_paths(tree, cfg_root)
    assert str(tree / "Folder" / "a.txt") in got_root
    assert str(tree / "X" / "Folder" / "b.txt") not in got_root
    assert str(tree / "A" / "B" / "Folder" / "c.txt") not in got_root

    cfg_one = make_config(include_dirs=["*/Folder"], include_extensions=[".*"])
    got_one = select_paths(tree, cfg_one)
    assert str(tree / "X" / "Folder" / "b.txt") in got_one
    assert str(tree / "Folder" / "a.txt") not in got_one
    assert str(tree / "A" / "B" / "Folder" / "c.txt") not in got_one

    cfg_any = make_config(include_dirs=["**/Folder"], include_extensions=[".*"])
    got_any = select_paths(tree, cfg_any)
    assert str(tree / "Folder" / "a.txt") in got_any
    assert str(tree / "X" / "Folder" / "b.txt") in got_any
    assert str(tree / "A" / "B" / "Folder" / "c.txt") in got_any


@pytest.mark.parametrize(
    "pattern,dirpath,expected",
    [
        ("folder", "folder", True),
        ("folder", "folder/sub", False),
        ("folder", "other/folder", False),
        ("folder/*", "folder/a", True),
        ("folder/*", "folder/a/b", False),
        ("folder/**", "folder/x/y", True),
        ("folder/**/sub", "folder/a/b/sub", True),
        ("folder/**/sub", "folder/sub", True),
        ("*/folder", "src/folder", True),
        ("*/folder", "folder", False),
        ("*/*/folder", "a/b/folder", True),
        ("*/*/folder", "a/folder", False),
        ("**/folder", "a/b/c/folder", True),
        ("**/folder", "folder", True),
        ("**", "", True),
        ("**/**", "any/nested/path", True),
        ("folder/*/another", "folder/x/another", True),
        ("folder/*/another", "folder/x/y/another", False),
        ("folder/**/another", "folder/x/y/another", True),
        ("folder/**/another", "folder/another", True),
        ("folder/***/another", "folder/***/another", True),
        ("folder/***/another", "folder/x/another", False),
        ("**/*hello/**", "abc/myhello/efg", True),
        ("**/*hello/**", "abc/hello/efg", False),
        ("**/**hello/**", "abc/hello/efg", True),
        ("**/**hello/**", "abc/myhello/efg", True),
        ("**/*hello/**", "abc/xhello/efg", True),
        ("**/hello*/**", "abc/helloworld/x", True),
        ("**/hello*/**", "abc/hello/x", False),
        ("**/*abc/**", "xyz/dataabc/nested", True),
        ("**/abc*/**", "xyz/abc123/nested", True),
        ("**/*abc*", "somewhere/myabcfolder", True),
    ],
)
def test_match_dir_patterns(pattern: str, dirpath: str, expected: bool):
    assert match_dir(dirpath, [pattern]) is expected


def test_exclude_dirs_with_segment_glob(tmp_path: Path):
    touch(tmp_path / "ok" / "file.c")
    touch(tmp_path / "ABC" / "Myhello" / "EFG" / "skip.c")
    touch(tmp_path / "ABC" / "hello" / "EFG" / "skip.c")
    touch(tmp_path / "ABC" / "xhello" / "keep.c")

    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["c"],
        exclude_dirs=["**/*hello/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "ok" / "file.c") in paths
    assert str(tmp_path / "ABC" / "Myhello" / "EFG" / "skip.c") not in paths
    assert str(tmp_path / "ABC" / "xhello" / "keep.c") not in paths
    assert str(tmp_path / "ABC" / "hello" / "EFG" / "skip.c") in paths


def test_exclude_dirs_segment_glob_includes_bare_hello_with_doublestar(tmp_path: Path):
    touch(tmp_path / "ABC" / "hello" / "EFG" / "skip.c")
    touch(tmp_path / "ABC" / "Myhello" / "EFG" / "skip.c")
    touch(tmp_path / "ok" / "file.c")

    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["c"],
        exclude_dirs=["**/**hello/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "ok" / "file.c") in paths
    assert str(tmp_path / "ABC" / "hello" / "EFG" / "skip.c") not in paths
    assert str(tmp_path / "ABC" / "Myhello" / "EFG" / "skip.c") not in paths

def test_match_file_dir_segment_glob(tmp_path: Path):
    touch(tmp_path / "ABC" / "Myhello" / "target.c")
    touch(tmp_path / "ABC" / "hello" / "target.c")
    cfg = make_config(
        include_files=["**/*hello/**/target.c"],
        include_extensions=["c"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "ABC" / "Myhello" / "target.c") in paths
    assert str(tmp_path / "ABC" / "hello" / "target.c") not in paths


def test_root_only_dir_pattern_does_not_match_nested_descendants(tree: Path):
    cfg = make_config(include_dirs=["folder"], include_extensions=[".*"])
    paths = select_paths(tree, cfg)
    assert str(tree / "folder" / "***" / "literal.txt") not in paths


@pytest.mark.parametrize(
    "pattern,filepath,expected",
    [
        ("Makefile", "Makefile", True),
        ("Makefile", "src/Makefile", False),
        ("**/Makefile", "src/Makefile", True),
        ("**", "any/depth/file.dat", True),
        ("**/**", "any/depth/file.dat", True),
        ("folder/*/file.txt", "folder/a/file.txt", True),
        ("folder/*/file.txt", "folder/a/b/file.txt", False),
        ("folder/**/file.txt", "folder/file.txt", True),
        ("folder/**/file.txt", "folder/a/b/file.txt", True),
        ("*/*/folder/*/another.py", "a/b/folder/c/another.py", True),
        ("*/*/folder/*/another.py", "a/b/folder/c/d/another.py", False),
        ("*/*/folder/**/another.py", "a/b/folder/another.py", True),
        ("*/*/folder/**/another.py", "a/b/folder/x/y/another.py", True),
        ("**/folder/***/file.txt", "folder/***/file.txt", True),
        ("**/folder/***/file.txt", "folder/x/file.txt", False),
        ("**/.env**", ".env", True),
        ("**/.env**", "app/.env.local", True),
        ("**/*.tar.**", "a.tar.gz", True),
        ("**/*.tar.**", "a/b/c.tar.", True),
        ("**/*.*", "a.txt", True),
        ("**/*.*", "noext", False),
        ("**/*.", "weird.", True),
    ],
)
def test_match_file_patterns(pattern: str, filepath: str, expected: bool):
    assert match_file(filepath, [pattern]) is expected


def test_case_insensitive_matching(tree: Path):
    touch(tree / "SRC" / "Mixed.CASE.PY")
    cfg = make_config(include_files=["**/*.case.py"], include_extensions=[".*"])
    paths = select_paths(tree, cfg)
    assert str(tree / "SRC" / "Mixed.CASE.PY") in paths


def test_literal_triple_star_directory(tree: Path):
    cfg = make_config(
        include_files=["**/folder/***/literal.txt"],
        include_extensions=[".*"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "folder" / "***" / "literal.txt") in paths
    touch(tree / "folder" / "x" / "literal.txt")
    paths = select_paths(tree, cfg)
    assert str(tree / "folder" / "x" / "literal.txt") not in paths


def test_readme_doublestar_suffix_matches_bare_name(tmp_path: Path):
    touch(tmp_path / "README")
    touch(tmp_path / "README.md")
    cfg = make_config(include_files=["README.**"])
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "README") in paths
    assert str(tmp_path / "README.md") in paths
