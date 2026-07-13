from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import make_config, rules_for, select_paths, touch, tree  # noqa: F401
from filefilter import matches, scan


def test_empty_filters_include_everything(tree: Path):
    cfg = make_config()
    paths = select_paths(tree, cfg)
    assert str(tree / "main.py") in paths
    assert str(tree / "noext") in paths
    assert str(tree / "src" / "app.py") in paths


def test_extension_whitelist_only(tree: Path):
    cfg = make_config(include_extensions=["py"])
    paths = select_paths(tree, cfg)
    assert str(tree / "main.py") in paths
    assert str(tree / "src" / "app.py") in paths
    assert str(tree / "README.md") not in paths
    assert str(tree / "noext") not in paths


def test_extension_dot_star_requires_dot(tree: Path):
    cfg = make_config(include_extensions=[".*"])
    paths = select_paths(tree, cfg)
    assert str(tree / "main.py") in paths
    assert str(tree / "noext") not in paths
    # os.path.splitext('.env') yields no extension; extension ".*" is not the file pattern "/.*"
    assert str(tree / ".env") not in paths


def test_compound_extension_tar_gz(tmp_path: Path):
    touch(tmp_path / "archive.tar.gz")
    touch(tmp_path / "archive.tar")
    cfg = make_config(include_extensions=["tar.gz"])
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "archive.tar.gz") in paths
    assert str(tmp_path / "archive.tar") not in paths


def test_include_files_override_extension_whitelist(tree: Path):
    cfg = make_config(
        include_files=["README.md"],
        include_extensions=["py"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "README.md") in paths
    assert str(tree / "main.py") not in paths


def test_exclude_extension_wins_over_include_file(tree: Path):
    cfg = make_config(
        include_files=["skip.ext2"],
        exclude_extensions=[".ext2"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "A" / "01" / "skip.ext2") not in paths


def test_exclude_file_wins_over_include_file(tree: Path):
    cfg = make_config(
        include_files=["**/*.py"],
        exclude_files=["src/hi/**/hello.py"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "main.py") in paths
    assert str(tree / "src" / "hi" / "hello.py") not in paths
    assert str(tree / "src" / "hi" / "nested" / "hello.py") not in paths


def test_exclude_dir_blocks_descendants(tree: Path):
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["py"],
        exclude_dirs=["**/__pycache__/**"],
    )
    touch(tree / "src" / "__pycache__" / "cached.py")
    paths = select_paths(tree, cfg)
    assert str(tree / "src" / "app.py") in paths
    assert str(tree / "src" / "__pycache__" / "cached.py") not in paths


def test_include_dirs_gate_with_extension_whitelist(tree: Path):
    cfg = make_config(
        include_dirs=["src/**"],
        include_extensions=["py"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "src" / "app.py") in paths
    assert str(tree / "main.py") not in paths
    assert str(tree / "docs" / "guide.md") not in paths


def test_include_files_gate_without_matching_dir(tree: Path):
    cfg = make_config(
        include_files=["*/hi/**/hello.py"],
        include_extensions=["py"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "src" / "hi" / "hello.py") in paths
    assert str(tree / "hi" / "hello.py") not in paths
    touch(tree / "a" / "b" / "hi" / "hello.py")
    assert str(tree / "a" / "b" / "hi" / "hello.py") not in select_paths(tree, cfg)


def test_matches_single_path_api(tree: Path):
    rules = rules_for(tree, make_config(include_extensions=["py"]))
    assert matches(str(tree / "main.py"), rules) is True
    assert matches(str(tree / "README.md"), rules) is False


def test_symlinks_are_not_followed(tmp_path: Path):
    real = touch(tmp_path / "real" / "data.py")
    link_dir = tmp_path / "linked"
    link_dir.mkdir()
    link = link_dir / "data.py"
    try:
        os.symlink(real, link)
    except OSError:
        pytest.skip("symlinks not supported in this environment")

    cfg = make_config(include_extensions=["py"])
    paths = select_paths(tmp_path, cfg)
    assert str(real) in paths
    assert str(link) not in paths


def test_scan_returns_normpath_absolute_paths(tree: Path):
    rules = rules_for(tree, make_config(include_files=["main.py"]))
    result = scan(rules)
    assert len(result) == 1
    assert result[0] == os.path.normpath(str(tree / "main.py"))


def test_readme_example_exclude_hi_hello_pattern(tree: Path):
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=[".py"],
        exclude_files=["*/hi/**/hello.py"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "main.py") in paths
    assert str(tree / "src" / "lib" / "util.py") in paths
    assert str(tree / "src" / "hi" / "hello.py") not in paths
    touch(tree / "hi" / "hello.py")
    assert str(tree / "hi" / "hello.py") in select_paths(tree, cfg)


def test_exclude_only_filters_leave_other_files(tree: Path):
    cfg = make_config(exclude_extensions=["md"])
    paths = select_paths(tree, cfg)
    assert str(tree / "README.md") not in paths
    assert str(tree / "main.py") in paths
    assert str(tree / "noext") in paths


def test_include_dirs_or_files_either_can_gate(tree: Path):
    cfg = make_config(
        include_dirs=["docs"],
        include_files=["**/Makefile"],
        include_extensions=[".*"],
    )
    paths = select_paths(tree, cfg)
    assert str(tree / "docs" / "guide.md") in paths
    assert str(tree / "Makefile") in paths
    assert str(tree / "main.py") not in paths


def test_dotfile_file_pattern_not_extension_filter(tree: Path):
    cfg = make_config(include_files=["**/.*"], include_extensions=[])
    paths = select_paths(tree, cfg)
    assert str(tree / ".env") in paths
    assert str(tree / "main.py") not in paths


def test_specific_odir_beats_broader_exclude(tmp_path: Path):
    """Only include.odirs override excludes; include.dirs do not."""
    touch(tmp_path / "src" / "foo.c")
    touch(tmp_path / "src" / "KLM" / "skip.c")
    touch(tmp_path / "src" / "KLM" / "ABC" / "keep.c")
    touch(tmp_path / "src" / "KLM" / "ABC" / "deep" / "keep.c")
    touch(tmp_path / "src" / "x" / "KLM" / "ABC" / "keep.c")

    cfg = make_config(
        include_dirs=["**"],
        include_odirs=["**/KLM/ABC/**"],
        include_extensions=["c"],
        exclude_dirs=["**/KLM/**"],
    )
    paths = select_paths(tmp_path, cfg)

    assert str(tmp_path / "src" / "foo.c") in paths
    assert str(tmp_path / "src" / "KLM" / "skip.c") not in paths
    assert str(tmp_path / "src" / "KLM" / "ABC" / "keep.c") in paths
    assert str(tmp_path / "src" / "KLM" / "ABC" / "deep" / "keep.c") in paths
    assert str(tmp_path / "src" / "x" / "KLM" / "ABC" / "keep.c") in paths


def test_include_dirs_do_not_override_exclude(tmp_path: Path):
    touch(tmp_path / "src" / "KLM" / "ABC" / "keep.c")
    cfg = make_config(
        include_dirs=["**", "**/KLM/ABC/**"],
        include_extensions=["c"],
        exclude_dirs=["**/KLM/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "src" / "KLM" / "ABC" / "keep.c") not in paths


def test_broad_include_dir_does_not_beat_specific_exclude(tree: Path):
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["py"],
        exclude_dirs=["**/__pycache__/**"],
    )
    touch(tree / "src" / "__pycache__" / "cached.py")
    paths = select_paths(tree, cfg)
    assert str(tree / "src" / "app.py") in paths
    assert str(tree / "src" / "__pycache__" / "cached.py") not in paths


def test_abc_klm_exception_via_include_odirs(tmp_path: Path):
    """ABC/KLM carve-out uses include.odirs, not include.dirs."""
    touch(tmp_path / "src" / "foo.c")
    touch(tmp_path / "src" / "ABC" / "only.c")
    touch(tmp_path / "src" / "ABC" / "other" / "skip.c")
    touch(tmp_path / "src" / "ABC" / "KLM" / "keep.c")
    touch(tmp_path / "src" / "ABC" / "KLM" / "nested" / "keep.c")
    touch(tmp_path / "src" / "x" / "ABC" / "other" / "skip.c")
    touch(tmp_path / "src" / "x" / "ABC" / "KLM" / "keep.c")

    cfg = make_config(
        include_dirs=["src/**"],
        include_odirs=["**/ABC/KLM/**"],
        include_extensions=["c"],
        exclude_dirs=["**/ABC/**"],
    )
    paths = select_paths(tmp_path, cfg)

    assert str(tmp_path / "src" / "foo.c") in paths
    assert str(tmp_path / "src" / "ABC" / "only.c") not in paths
    assert str(tmp_path / "src" / "ABC" / "other" / "skip.c") not in paths
    assert str(tmp_path / "src" / "ABC" / "KLM" / "keep.c") in paths
    assert str(tmp_path / "src" / "ABC" / "KLM" / "nested" / "keep.c") in paths
    assert str(tmp_path / "src" / "x" / "ABC" / "other" / "skip.c") not in paths
    assert str(tmp_path / "src" / "x" / "ABC" / "KLM" / "keep.c") in paths
