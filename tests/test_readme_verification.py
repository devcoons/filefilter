"""Verify every file outcome documented in README Examples 1–7."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import touch
from filefilter import load, matches

README_EXAMPLES = [
    pytest.param(
        {
            "root_dir": ".",
            "filters": {
                "include": {"dirs": ["**"], "files": [], "extensions": ["py"]},
                "exclude": {"dirs": [], "files": [], "extensions": []},
            },
        },
        {
            "main.py": True,
            "src/app.py": True,
            "docs/readme.md": False,
            "a/b/c/module.py": True,
        },
        id="example-1-all-py",
    ),
    pytest.param(
        {
            "root_dir": ".",
            "filters": {
                "include": {"dirs": [], "files": ["*.py"], "extensions": []},
                "exclude": {"dirs": [], "files": [], "extensions": []},
            },
        },
        {
            "main.py": True,
            "helper.py": True,
            "src/app.py": False,
            "src/helper.py": False,
        },
        id="example-2-root-py-only",
    ),
    pytest.param(
        {
            "root_dir": ".",
            "filters": {
                "include": {"dirs": [], "files": ["*/hi/**/hello.py"], "extensions": []},
                "exclude": {"dirs": [], "files": [], "extensions": []},
            },
        },
        {
            "a/hi/hello.py": True,
            "a/hi/x/hello.py": True,
            "hi/hello.py": False,
            "a/b/hi/hello.py": False,
            "a/hi/hello.txt": False,
        },
        id="example-3-hi-hello",
    ),
    pytest.param(
        {
            "root_dir": ".",
            "filters": {
                "include": {"dirs": ["**"], "files": [], "extensions": [".py"]},
                "exclude": {"dirs": [], "files": ["*/hi/**/hello.py"], "extensions": []},
            },
        },
        {
            "main.py": True,
            "src/lib/module.py": True,
            "a/hi/hello.py": False,
            "src/hi/utils/hello.py": False,
            "hi/hello.py": True,
        },
        id="example-4-exclude-hi-hello",
    ),
    pytest.param(
        {
            "root_dir": ".",
            "filters": {
                "include": {"dirs": ["**/myfolder/**"], "files": [], "extensions": ["py"]},
                "exclude": {"dirs": ["**/__pycache__/**"], "files": [], "extensions": []},
            },
        },
        {
            "src/myfolder/x/hello.py": True,
            "src/myfolder/sub/a.py": True,
            "src/myfolder/__pycache__/cached.py": False,
            "src/other/hello.py": False,
        },
        id="example-5-myfolder",
    ),
    pytest.param(
        {
            "root_dir": ".",
            "filters": {
                "include": {
                    "dirs": ["src/**", "scripts"],
                    "files": ["**/*.sh", "*.py"],
                    "extensions": ["py", "sh"],
                },
                "exclude": {
                    "dirs": ["**/__pycache__/**", "build"],
                    "files": ["*/legacy/**"],
                    "extensions": ["log"],
                },
            },
        },
        {
            "src/main.py": True,
            "scripts/setup.sh": True,
            "build/config.py": False,
            "src/legacy/module.py": False,
            "docs/readme.md": False,
            "src/utils/tool.log": False,
        },
        id="example-6-complex",
    ),
    pytest.param(
        {
            "root_dir": ".",
            "filters": {
                "include": {"dirs": ["**", "**/KLM/ABC/**"], "files": [], "extensions": ["c"]},
                "exclude": {"dirs": ["**/KLM/**"], "files": [], "extensions": []},
            },
        },
        {
            "src/foo.c": True,
            "src/KLM/skip.c": False,
            "src/KLM/ABC/keep.c": True,
            "src/x/KLM/ABC/deep/keep.c": True,
            "src/KLM/ABC/keep.txt": False,
        },
        id="example-7-klm-abc-exception",
    ),
]


@pytest.mark.parametrize("cfg,expected", README_EXAMPLES)
def test_readme_documented_examples(tmp_path: Path, cfg: dict, expected: dict[str, bool]):
    for rel in expected:
        touch(tmp_path / rel)
    rules = load(json.dumps(cfg), base=str(tmp_path))
    for rel, should_match in expected.items():
        assert matches(str(tmp_path / rel), rules) is should_match, rel


def test_readme_decision_order_extension_exclude_is_hard(tmp_path: Path):
    touch(tmp_path / "keep.log")
    cfg = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": ["**/special/**"], "files": [], "extensions": ["log"]},
            "exclude": {"dirs": ["**"], "files": [], "extensions": ["log"]},
        },
    }
    rules = load(json.dumps(cfg), base=str(tmp_path))
    # include dir is more specific, but extension exclude is hard
    touch(tmp_path / "special" / "keep.log")
    assert matches(str(tmp_path / "special" / "keep.log"), rules) is False


def test_readme_decision_order_include_files_skip_extension_whitelist(tmp_path: Path):
    touch(tmp_path / "readme.md")
    cfg = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": [], "files": ["README.md"], "extensions": ["py"]},
            "exclude": {"dirs": [], "files": [], "extensions": []},
        },
    }
    rules = load(json.dumps(cfg), base=str(tmp_path))
    assert matches(str(tmp_path / "readme.md"), rules) is True


def test_readme_abc_klm_branch_exception(tmp_path: Path):
    layout = {
        "src/foo.c": True,
        "src/ABC/only.c": False,
        "src/ABC/other/skip.c": False,
        "src/ABC/KLM/keep.c": True,
        "src/ABC/KLM/nested/keep.c": True,
        "src/x/ABC/other/skip.c": False,
        "src/x/ABC/KLM/keep.c": True,
    }
    for rel in layout:
        touch(tmp_path / rel)
    cfg = {
        "root_dir": ".",
        "filters": {
            "include": {"dirs": ["src/**", "**/ABC/KLM/**"], "files": [], "extensions": ["c"]},
            "exclude": {"dirs": ["**/ABC/**"], "files": [], "extensions": []},
        },
    }
    rules = load(json.dumps(cfg), base=str(tmp_path))
    for rel, expected in layout.items():
        assert matches(str(tmp_path / rel), rules) is expected, rel
