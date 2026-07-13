from __future__ import annotations

import json
from pathlib import Path

import pytest

from filefilter import Ruleset, load, matches, scan, select


def touch(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("")
    return p


def norm_paths(paths: list[str]) -> list[str]:
    return sorted(str(Path(p)) for p in paths)


def make_config(
    *,
    include_dirs: list[str] | None = None,
    include_odirs: list[str] | None = None,
    include_files: list[str] | None = None,
    include_extensions: list[str] | None = None,
    exclude_dirs: list[str] | None = None,
    exclude_files: list[str] | None = None,
    exclude_extensions: list[str] | None = None,
    root_dir: str = ".",
) -> dict:
    return {
        "root_dir": root_dir,
        "filters": {
            "include": {
                "dirs": include_dirs or [],
                "odirs": include_odirs or [],
                "files": include_files or [],
                "extensions": include_extensions or [],
            },
            "exclude": {
                "dirs": exclude_dirs or [],
                "files": exclude_files or [],
                "extensions": exclude_extensions or [],
            },
        },
    }


def select_paths(tmp_path: Path, cfg: dict) -> set[str]:
    return set(norm_paths(select(json.dumps(cfg), base=str(tmp_path))))


def rules_for(tmp_path: Path, cfg: dict) -> Ruleset:
    return load(json.dumps(cfg), base=str(tmp_path))


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Small deterministic tree used across several tests."""
    touch(tmp_path / "Makefile")
    touch(tmp_path / "main.py")
    touch(tmp_path / "README.md")
    touch(tmp_path / "report_2025.csv")
    touch(tmp_path / "report_")
    touch(tmp_path / ".env")
    touch(tmp_path / "noext")
    touch(tmp_path / "A" / "01" / "x.txt")
    touch(tmp_path / "A" / "01" / "skip.ext2")
    touch(tmp_path / "A" / "03" / "y.txt")
    touch(tmp_path / "B" / "01" / "03" / "z.txt")
    touch(tmp_path / "src" / "app.py")
    touch(tmp_path / "src" / "lib" / "util.py")
    touch(tmp_path / "src" / "hi" / "hello.py")
    touch(tmp_path / "src" / "hi" / "nested" / "hello.py")
    touch(tmp_path / "docs" / "guide.md")
    touch(tmp_path / "Folder" / "a.txt")
    touch(tmp_path / "X" / "Folder" / "b.txt")
    touch(tmp_path / "A" / "B" / "Folder" / "c.txt")
    touch(tmp_path / "folder" / "***" / "literal.txt")
    touch(tmp_path / "pkg" / "LICENSE")
    touch(tmp_path / "pkg" / "LICENSE-MIT")
    touch(tmp_path / "deep" / "x" / "y" / "fileA.py")
    touch(tmp_path / "deep" / "x" / "y" / "file.py")
    return tmp_path
