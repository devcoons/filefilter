# test_filefilter.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

from filefilter import filter_paths


def _touch(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("")  # empty file
    return p


def _norm_paths(paths: list[str]) -> list[str]:
    # Normalize separators & sort for deterministic comparisons
    return sorted(str(Path(p)) for p in paths)


def test_filter_paths_basic_semantics(tmp_path: Path):
    """
    Covers:
      - include.dirs: "**/01/**"
      - include.files: ["report_*"] (with '*' requiring at least one char; report_ should NOT match)
      - include.extensions: [".*"] (any extension with a dot)
      - exclude.extensions: [".ext2"]
    """

    # Layout
    # <tmp>/
    #   report_2025.csv               -> should match include.files
    #   report_                        -> should NOT match "report_*"
    #   A/01/x.txt                     -> should be included (dir include + ext include)
    #   A/01/skip.ext2                 -> should be excluded by ext
    #   A/03/y.txt                     -> should NOT be included (dir include targets 01/**)
    #   B/01/03/z.txt                  -> should be included (matches **/01/**)
    _touch(tmp_path / "report_2025.csv")
    _touch(tmp_path / "report_")
    _touch(tmp_path / "A" / "01" / "x.txt")
    _touch(tmp_path / "A" / "01" / "skip.ext2")
    _touch(tmp_path / "A" / "03" / "y.txt")
    _touch(tmp_path / "B" / "01" / "03" / "z.txt")

    cfg = {
        "root_dir": ".",  # resolved against resolve_base below
        "filters": {
            "include": {
                "dirs": ["**/01/**"],
                "files": ["report_*"],
                "extensions": [".*"],
            },
            "exclude": {
                "dirs": [],
                "files": [],
                "extensions": [".ext2"],
            },
        },
    }
    content = json.dumps(cfg)

    # IMPORTANT: pass a string path for resolve_base
    got = _norm_paths(filter_paths(content, resolve_base=str(tmp_path)))

    expect = _norm_paths(
        [
            str(tmp_path / "report_2025.csv"),
            str(tmp_path / "A" / "01" / "x.txt"),
            str(tmp_path / "B" / "01" / "03" / "z.txt"),
        ]
    )
    assert got == expect


@pytest.mark.parametrize(
    "fname,patterns,expected",
    [
        ("report_", ["report_*"], False),     # '*' must match 1+ chars
        ("report_", ["report_**"], True),     # '**' may match 0+ chars
        ("x/file.txt", ["file.txt"], False),  # root-only file
        ("x/file.txt", ["*/file.txt"], True), # exactly one level
        ("x/y/file.txt", ["*/*/file.txt"], True),
        ("x/y/file.txt", ["**/file.txt"], True),
    ],
)
def test_file_location_and_star_semantics(tmp_path: Path, fname: str, patterns: list[str], expected: bool):
    # Make structure
    target = tmp_path / fname
    _touch(target)

    cfg = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": [], "files": patterns, "extensions": [".*"]},
            "exclude": {"dirs": [], "files": [], "extensions": []},
        },
    }
    content = json.dumps(cfg)
    got = filter_paths(content, resolve_base=str(tmp_path))
    paths = set(_norm_paths(got))
    assert (str(target) in paths) is expected


def test_dir_root_one_any_semantics(tmp_path: Path):
    # Root-only: Folder; One-level: */Folder; Anywhere: **/Folder
    _touch(tmp_path / "Folder" / "a.txt")          # root/Folder/a.txt
    _touch(tmp_path / "X" / "Folder" / "b.txt")    # one-level
    _touch(tmp_path / "A" / "B" / "Folder" / "c.txt")  # anywhere

    # 1) root-only dir exact
    cfg1 = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": ["Folder"], "files": [], "extensions": [".*"]},
            "exclude": {"dirs": [], "files": [], "extensions": []},
        },
    }
    got1 = _norm_paths(filter_paths(json.dumps(cfg1), resolve_base=str(tmp_path)))
    assert str(tmp_path / "Folder" / "a.txt") in got1
    assert str(tmp_path / "X" / "Folder" / "b.txt") not in got1
    assert str(tmp_path / "A" / "B" / "Folder" / "c.txt") not in got1

    # 2) exactly one level under root
    cfg2 = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": ["*/Folder"], "files": [], "extensions": [".*"]},
            "exclude": {"dirs": [], "files": [], "extensions": []},
        },
    }
    got2 = _norm_paths(filter_paths(json.dumps(cfg2), resolve_base=str(tmp_path)))
    assert str(tmp_path / "X" / "Folder" / "b.txt") in got2
    assert str(tmp_path / "Folder" / "a.txt") not in got2
    assert str(tmp_path / "A" / "B" / "Folder" / "c.txt") not in got2

    # 3) anywhere
    cfg3 = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": ["**/Folder"], "files": [], "extensions": [".*"]},
            "exclude": {"dirs": [], "files": [], "extensions": []},
        },
    }
    got3 = _norm_paths(filter_paths(json.dumps(cfg3), resolve_base=str(tmp_path)))
    assert str(tmp_path / "Folder" / "a.txt") in got3
    assert str(tmp_path / "X" / "Folder" / "b.txt") in got3
    assert str(tmp_path / "A" / "B" / "Folder" / "c.txt") in got3
