"""Exhaustive three-pass pipeline tests: scope -> exclude -> override."""

from __future__ import annotations

from pathlib import Path

import pytest

from filefilter import dry_run, load, matches, scan
from conftest import make_config, select_paths, touch


# ---------------------------------------------------------------------------
# Pass 1 — include.dirs / include.files scope
# ---------------------------------------------------------------------------


def test_pass1_empty_include_allows_all(tmp_path: Path):
    touch(tmp_path / "anywhere" / "file.py")
    touch(tmp_path / "other.txt")
    cfg = make_config(include_extensions=["py", "txt"])
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "anywhere" / "file.py") in paths
    assert str(tmp_path / "other.txt") in paths


def test_pass1_include_dirs_rejects_out_of_scope_before_exclude(tmp_path: Path):
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "docs" / "readme.md")
    cfg = make_config(
        include_dirs=["src/**"],
        include_extensions=["py", "md"],
        exclude_dirs=["**/docs/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "src" / "app.py") in paths
    assert str(tmp_path / "docs" / "readme.md") not in paths


def test_pass1_include_files_or_dirs_either_in_scope(tmp_path: Path):
    touch(tmp_path / "Makefile")
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "docs" / "guide.md")
    cfg = make_config(
        include_dirs=["src/**"],
        include_files=["Makefile"],
        include_extensions=[".*"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "Makefile") in paths
    assert str(tmp_path / "src" / "app.py") in paths
    assert str(tmp_path / "docs" / "guide.md") not in paths


def test_pass1_odirs_do_not_define_scope(tmp_path: Path):
    """odirs override excludes only; they do not replace include.dirs for scoping."""
    touch(tmp_path / "src" / "in.py")
    touch(tmp_path / "other" / "out.py")
    cfg = make_config(
        include_dirs=[],
        include_odirs=["src/**"],
        include_extensions=["py"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "src" / "in.py") in paths
    assert str(tmp_path / "other" / "out.py") in paths


# ---------------------------------------------------------------------------
# Pass 2 — exclude.dirs / exclude.files
# ---------------------------------------------------------------------------


def test_pass2_exclude_dir_blocks_descendants(tmp_path: Path):
    touch(tmp_path / "build" / "out.o")
    touch(tmp_path / "build" / "nested" / "out.o")
    touch(tmp_path / "src" / "app.c")
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["c", "o"],
        exclude_dirs=["**/build/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "src" / "app.c") in paths
    assert str(tmp_path / "build" / "out.o") not in paths
    assert str(tmp_path / "build" / "nested" / "out.o") not in paths


def test_pass2_exclude_file_pattern(tmp_path: Path):
    touch(tmp_path / "keep.py")
    touch(tmp_path / "test_a.py")
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["py"],
        exclude_files=["**/test_*.py"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "keep.py") in paths
    assert str(tmp_path / "test_a.py") not in paths


def test_pass2_both_dir_and_file_exclude(tmp_path: Path):
    touch(tmp_path / "vendor" / "secret" / "key.pem")
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["pem"],
        exclude_dirs=["**/secret/**"],
        exclude_files=["**/*.pem"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "vendor" / "secret" / "key.pem") not in paths


# ---------------------------------------------------------------------------
# Pass 3 — odirs / ofiles undo excludes
# ---------------------------------------------------------------------------


def test_pass3_odir_carves_dir_exclude(tmp_path: Path):
    touch(tmp_path / "src" / "KLM" / "skip.c")
    touch(tmp_path / "src" / "KLM" / "ABC" / "keep.c")
    cfg = make_config(
        include_dirs=["**"],
        include_odirs=["**/KLM/ABC/**"],
        include_extensions=["c"],
        exclude_dirs=["**/KLM/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "src" / "KLM" / "skip.c") not in paths
    assert str(tmp_path / "src" / "KLM" / "ABC" / "keep.c") in paths


def test_pass3_ofile_carves_file_exclude(tmp_path: Path):
    touch(tmp_path / "test_foo.py")
    touch(tmp_path / "nested" / "test_keep.py")
    cfg = make_config(
        include_dirs=["**"],
        include_ofiles=["**/test_keep.py"],
        include_extensions=["py"],
        exclude_files=["**/test_*.py"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "test_foo.py") not in paths
    assert str(tmp_path / "nested" / "test_keep.py") in paths


def test_pass3_same_pattern_odir_wins_over_exclude(tmp_path: Path):
    """Matching odir undoes exclude even when patterns are equally broad."""
    touch(tmp_path / "KLM" / "keep.c")
    cfg = make_config(
        include_dirs=["**"],
        include_odirs=["**/KLM/**"],
        include_extensions=["c"],
        exclude_dirs=["**/KLM/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "KLM" / "keep.c") in paths


def test_pass3_broad_ofile_undoes_narrow_file_exclude(tmp_path: Path):
    touch(tmp_path / "secrets" / "credentials.json")
    touch(tmp_path / "data" / "public.json")
    cfg = make_config(
        include_dirs=["**"],
        include_ofiles=["**/*.json"],
        include_extensions=["json"],
        exclude_files=["**/credentials.json"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "secrets" / "credentials.json") in paths
    assert str(tmp_path / "data" / "public.json") in paths


def test_pass3_odir_undoes_file_exclude_when_dir_matches(tmp_path: Path):
    touch(tmp_path / "legacy" / "test_old.py")
    cfg = make_config(
        include_dirs=["**"],
        include_odirs=["**/legacy/**"],
        include_extensions=["py"],
        exclude_files=["**/test_*.py"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "legacy" / "test_old.py") in paths


def test_pass3_ofile_undoes_dir_exclude_for_one_file(tmp_path: Path):
    touch(tmp_path / "build" / "app.py")
    touch(tmp_path / "build" / "keep.py")
    cfg = make_config(
        include_dirs=["**"],
        include_ofiles=["**/build/keep.py"],
        include_extensions=["py"],
        exclude_dirs=["**/build/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "build" / "app.py") not in paths
    assert str(tmp_path / "build" / "keep.py") in paths


def test_pass3_no_override_stays_excluded(tmp_path: Path):
    touch(tmp_path / "skip" / "only.py")
    cfg = make_config(
        include_dirs=["**"],
        include_odirs=["**/keep/**"],
        include_extensions=["py"],
        exclude_dirs=["**/skip/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "skip" / "only.py") not in paths


# ---------------------------------------------------------------------------
# include.dirs/files never override excludes (need odirs/ofiles)
# ---------------------------------------------------------------------------


def test_include_dirs_do_not_override_exclude(tmp_path: Path):
    touch(tmp_path / "KLM" / "ABC" / "keep.c")
    cfg = make_config(
        include_dirs=["**", "**/KLM/ABC/**"],
        include_extensions=["c"],
        exclude_dirs=["**/KLM/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "KLM" / "ABC" / "keep.c") not in paths


def test_include_files_do_not_override_exclude(tmp_path: Path):
    touch(tmp_path / "test_keep.py")
    cfg = make_config(
        include_dirs=["**"],
        include_files=["**/test_keep.py"],
        include_extensions=["py"],
        exclude_files=["**/test_*.py"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "test_keep.py") not in paths


# ---------------------------------------------------------------------------
# Extension rules + fast path
# ---------------------------------------------------------------------------


def test_exclude_extensions_hard_not_overridden_by_odir(tmp_path: Path):
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "src" / "skip.log")
    cfg = make_config(
        include_dirs=["**"],
        include_odirs=["**/src/**"],
        include_extensions=["py"],
        exclude_extensions=["log"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "src" / "app.py") in paths
    assert str(tmp_path / "src" / "skip.log") not in paths


def test_include_files_fast_path_skips_extension_whitelist(tmp_path: Path):
    touch(tmp_path / "readme.md")
    cfg = make_config(
        include_dirs=["**"],
        include_files=["**/readme.md"],
        include_extensions=["py"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "readme.md") in paths


def test_ofile_does_not_skip_extension_whitelist(tmp_path: Path):
    touch(tmp_path / "keep.txt")
    cfg = make_config(
        include_dirs=["**"],
        include_ofiles=["**/keep.txt"],
        include_extensions=["py"],
        exclude_files=["**/*.txt"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "keep.txt") not in paths


# ---------------------------------------------------------------------------
# README-style scenarios
# ---------------------------------------------------------------------------


def test_readme_klm_abc_carve_out(tmp_path: Path):
    files = {
        "src/foo.c": True,
        "src/KLM/skip.c": False,
        "src/KLM/ABC/keep.c": True,
        "src/x/KLM/ABC/deep/keep.c": True,
        "src/KLM/ABC/keep.txt": False,
    }
    for rel in files:
        touch(tmp_path / rel)
    cfg = make_config(
        include_dirs=["**"],
        include_odirs=["**/KLM/ABC/**"],
        include_extensions=["c"],
        exclude_dirs=["**/KLM/**"],
    )
    paths = select_paths(tmp_path, cfg)
    for rel, expected in files.items():
        assert (str(tmp_path / rel) in paths) is expected, rel


def test_readme_abc_klm_branch(tmp_path: Path):
    files = {
        "src/foo.c": True,
        "src/ABC/only.c": False,
        "src/ABC/other/skip.c": False,
        "src/ABC/KLM/keep.c": True,
        "src/ABC/KLM/nested/keep.c": True,
        "src/x/ABC/other/skip.c": False,
        "src/x/ABC/KLM/keep.c": True,
    }
    for rel in files:
        touch(tmp_path / rel)
    cfg = make_config(
        include_dirs=["src/**"],
        include_odirs=["**/ABC/KLM/**"],
        include_extensions=["c"],
        exclude_dirs=["**/ABC/**"],
    )
    paths = select_paths(tmp_path, cfg)
    for rel, expected in files.items():
        assert (str(tmp_path / rel) in paths) is expected, rel


# ---------------------------------------------------------------------------
# API consistency: matches / scan / dry_run
# ---------------------------------------------------------------------------


def test_matches_agrees_with_scan(tmp_path: Path):
    touch(tmp_path / "a.py")
    touch(tmp_path / "b.log")
    touch(tmp_path / "build" / "c.py")
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["py"],
        exclude_dirs=["**/build/**"],
    )
    rules = load(__import__("json").dumps(cfg), base=str(tmp_path))
    selected = set(scan(rules))
    for path in [tmp_path / "a.py", tmp_path / "b.log", tmp_path / "build" / "c.py"]:
        assert (str(path) in selected) is matches(str(path), rules)


def test_dry_run_included_matches_scan(tmp_path: Path):
    touch(tmp_path / "src" / "a.py")
    touch(tmp_path / "src" / "b.py")
    cfg = make_config(
        include_dirs=["src/**"],
        include_extensions=["py"],
        exclude_files=["**/b.py"],
        include_ofiles=["**/b.py"],
    )
    import json

    rules = load(json.dumps(cfg), base=str(tmp_path))
    report = dry_run(rules)
    assert set(report.included) == set(scan(rules))


# ---------------------------------------------------------------------------
# Parametrized edge-case matrix
# ---------------------------------------------------------------------------

PASS_MATRIX = [
    pytest.param(
        {"include_dirs": ["src/**"], "include_extensions": ["py"]},
        {"exclude_dirs": ["**/tmp/**"]},
        {"include_odirs": ["**/tmp/safe/**"]},
        {
            "src/app.py": True,
            "src/tmp/skip.py": False,
            "src/tmp/safe/keep.py": True,
            "other/app.py": False,
        },
        id="scope-then-exclude-then-odir",
    ),
    pytest.param(
        {"include_dirs": ["**"], "include_extensions": ["py", "md"]},
        {"exclude_files": ["**/*.md"]},
        {"include_ofiles": ["**/README.md"]},
        {
            "docs/guide.md": False,
            "README.md": True,
            "pkg/README.md": True,
        },
        id="ofile-readme-carve-out",
    ),
    pytest.param(
        {"include_files": ["**/*.go"], "include_extensions": ["go"]},
        {},
        {},
        {"main.go": True, "main.py": False},
        id="files-only-scope",
    ),
    pytest.param(
        {"include_dirs": ["**"], "include_extensions": [".*"]},
        {"exclude_dirs": ["**/__pycache__/**"]},
        {},
        {
            "src/app.py": True,
            "src/__pycache__/x.py": False,
        },
        id="pycache-no-override",
    ),
]


@pytest.mark.parametrize("inc_kw,exc_kw,override_kw,files", PASS_MATRIX)
def test_three_pass_matrix(
    tmp_path: Path,
    inc_kw: dict,
    exc_kw: dict,
    override_kw: dict,
    files: dict[str, bool],
):
    for rel in files:
        touch(tmp_path / rel)
    cfg = make_config(
        include_dirs=inc_kw.get("include_dirs"),
        include_files=inc_kw.get("include_files"),
        include_extensions=inc_kw.get("include_extensions", ["py"]),
        exclude_dirs=exc_kw.get("exclude_dirs"),
        exclude_files=exc_kw.get("exclude_files"),
        include_odirs=override_kw.get("include_odirs"),
        include_ofiles=override_kw.get("include_ofiles"),
    )
    paths = select_paths(tmp_path, cfg)
    for rel, expected in files.items():
        assert (str(tmp_path / rel) in paths) is expected, rel
