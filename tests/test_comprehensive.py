"""
Exhaustive behavioural tests beyond line coverage — README tables, segment
globs, specificity, regressions, and end-to-end selection outcomes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import make_config, select_paths, touch
from filefilter import match_dir, match_file, matches
from filefilter.utilities import segment_matches

# ---------------------------------------------------------------------------
# Segment glob matrix
# ---------------------------------------------------------------------------

SEGMENT_GLOB_CASES = [
    # suffix glob *hello
    ("*hello", "myhello", True),
    ("*hello", "xhello", True),
    ("*hello", "hello", False),
    ("*hello", "helloworld", False),
    ("*hello", "notmatch", False),
    # suffix glob **hello (0+ prefix)
    ("**hello", "hello", True),
    ("**hello", "myhello", True),
    ("**hello", "xhello", True),
    ("**hello", "helloworld", False),
    # prefix glob hello*
    ("hello*", "helloworld", True),
    ("hello*", "hellox", True),
    ("hello*", "hello", False),
    # prefix glob hello**
    ("hello**", "hello", True),
    ("hello**", "helloworld", True),
    ("hello**", "myhello", False),
    # prefix *abc / suffix abc*
    ("*abc", "xabc", True),
    ("*abc", "myabc", True),
    ("*abc", "abc", False),
    ("abc*", "abcx", True),
    ("abc*", "abc123", True),
    ("abc*", "abc", False),
    # infix *abc*
    ("*abc*", "xabcy", True),
    ("*abc*", "dataabcdata", True),
    ("*abc*", "abc", False),
    ("*abc*", "ab", False),
    # **abc / abc** (0+ on one side)
    ("**abc", "abc", True),
    ("**abc", "xabc", True),
    ("abc**", "abc", True),
    ("abc**", "abcd", True),
    ("**abc**", "abc", True),
    ("**abc**", "xabcy", True),
    ("**abc**", "xab", False),
    # literals
    ("folder", "folder", True),
    ("folder", "Folder", True),
    ("folder", "other", False),
    ("***", "***", True),
    ("***", "**", False),
    ("***", "****", False),
    ("***", "myhello", False),
    # mixed literal + glob
    ("pre*fix", "preabcfix", True),
    ("pre*fix", "prefix", False),
    ("pre**fix", "prefix", True),
    ("pre**fix", "preabcfix", True),
]


@pytest.mark.parametrize("token,part,expected", SEGMENT_GLOB_CASES)
def test_segment_glob_matrix(token: str, part: str, expected: bool):
    assert segment_matches(token, part) is expected


# ---------------------------------------------------------------------------
# README folder-pattern table (match_dir)
# ---------------------------------------------------------------------------

README_DIR_PATTERNS = [
    ("folder", "folder", True),
    ("folder", "folder/sub", False),
    ("folder/*", "folder/a", True),
    ("folder/*", "folder/a/b", False),
    ("folder/*/*", "folder/a/b", True),
    ("folder/*/*", "folder/a", False),
    ("folder/**", "folder/x/y", True),
    ("folder/**/sub", "folder/a/b/sub", True),
    ("folder/**/sub", "folder/sub", True),
    ("*/folder", "src/folder", True),
    ("*/folder", "folder", False),
    ("*/folder/**", "src/folder/x/y", True),
    ("*/*/folder", "apps/web/folder", True),
    ("*/*/folder", "apps/folder", False),
    ("*/*/*/folder", "a/b/c/folder", True),
    ("*/*/*/*/folder/**", "a/b/c/d/folder/x/y", True),
    ("**/folder", "a/b/c/folder", True),
    ("**/folder", "folder", True),
    ("**/folder/**", "x/y/folder/z", True),
    ("**/folder/another", "folder/another", True),
    ("**/folder/another", "x/folder/another", True),
    ("**/pkg/*", "pkg/a", True),
    ("**/pkg/*", "x/y/pkg/z", True),
    ("**/pkg/*", "pkg/a/b", False),
    ("**/pkg/*/*", "pkg/a/b", True),
    ("**/pkg/*/*", "x/y/pkg/z/t", True),
    ("**/pkg/*/*", "pkg/a", False),
    ("modules/*/test", "modules/auth/test", True),
    ("modules/*/test", "modules/auth/pay/test", False),
    ("apps/**/dist", "apps/web/dist", True),
    ("apps/**/dist", "apps/mobile/a/b/dist", True),
    ("apps/**/dist", "other/dist", False),
    ("*/*/folder/*/another_folder", "a/b/folder/c/another_folder", True),
    ("*/*/folder/*/another_folder", "a/b/folder/c/d/another_folder", False),
    ("*/*/folder/**/another_folder", "a/b/folder/another_folder", True),
    ("*/*/folder/**/another_folder", "a/b/folder/x/another_folder", True),
    ("*/*/folder/*/*/another_folder", "a/b/folder/x/y/another_folder", True),
    ("*/*/folder/*/*/another_folder", "a/b/folder/x/another_folder", False),
    ("**/services/**/migrations/*", "services/migrations/2", True),
    ("**/services/**/migrations/*", "x/services/a/migrations/001", True),
    ("**/services/**/migrations/*", "services/m/2", False),
    ("**/features/*/*", "a/features/x/y", True),
    ("**/features/*/*", "features/p/q", True),
    ("**/features/*/*", "features/p/q/r", False),
    ("packages/*/**/dist", "packages/core/dist", True),
    ("packages/*/**/dist", "packages/ui/x/y/dist", True),
    ("packages/*/**/dist", "packages/dist", False),
    ("**/folder/***/anotherfolder", "folder/***/anotherfolder", True),
    ("**/folder/***/anotherfolder", "folder/x/anotherfolder", False),
    # segment globs in dir patterns
    ("**/*hello/**", "abc/myhello/efg", True),
    ("**/*hello/**", "abc/hello/efg", False),
    ("**/**hello/**", "abc/hello/efg", True),
    ("**/**hello/**", "abc/myhello/efg", True),
    ("**/hello*/**", "abc/helloworld/x", True),
    ("**/hello*/**", "abc/hello/x", False),
    ("**/hello**/**", "abc/hello/x", True),
    ("**/*abc/**", "data/myabc/nested", True),
    ("**/abc*/**", "data/abc123/nested", True),
]


@pytest.mark.parametrize("pattern,dirpath,expected", README_DIR_PATTERNS)
def test_readme_folder_pattern_table(pattern: str, dirpath: str, expected: bool):
    assert match_dir(dirpath, [pattern]) is expected


# ---------------------------------------------------------------------------
# README file-pattern table (match_file)
# ---------------------------------------------------------------------------

README_FILE_PATTERNS = [
    ("file.py", "file.py", True),
    ("file.py", "src/file.py", False),
    ("README.*", "README.md", True),
    ("README.*", "README.rst", True),
    ("README.*", "README", False),
    ("README.**", "README", True),
    ("README.**", "README.md", True),
    (".*", ".env", True),
    (".*", ".gitignore", True),
    (".*", "env", False),
    ("folder/*.py", "folder/a.py", True),
    ("folder/*.py", "folder/sub/a.py", False),
    ("folder/**/test_*.py", "folder/test_a.py", True),
    ("folder/**/test_*.py", "folder/x/y/test_utils.py", True),
    ("Makefile", "Makefile", True),
    ("Makefile", "src/Makefile", False),
    ("*.toml", "pyproject.toml", True),
    ("*.toml", "pkg/a/config.toml", False),
    ("**/*.toml", "pyproject.toml", True),
    ("**/*.toml", "pkg/a/b/config.toml", True),
    ("folder/**/*.md", "folder/README.md", True),
    ("folder/**/*.md", "folder/docs/a/b/guide.md", True),
    ("*/Dockerfile", "api/Dockerfile", True),
    ("*/Dockerfile", "Dockerfile", False),
    ("*/LICENSE*", "pkg/LICENSE-MIT", True),
    ("*/LICENSE*", "pkg/LICENSE", False),
    ("*/*/Makefile", "x/y/Makefile", True),
    ("*/*/Makefile", "x/Makefile", False),
    ("*/*/*/package.json", "a/b/c/package.json", True),
    ("**/Makefile", "Makefile", True),
    ("**/Makefile", "a/b/c/Makefile", True),
    ("**/*.py", "a.py", True),
    ("**/*.py", "pkg/mod/x.py", True),
    ("**", "any/depth/file.dat", True),
    ("src/**/test_*.py", "src/test_a.py", True),
    ("src/**/test_*.py", "src/unit/core/test_utils.py", True),
    ("**/migrations/*", "app/migrations/001.sql", True),
    ("**/migrations/*", "app/migrations/v1/001.sql", False),
    ("**/migrations/*/*", "app/migrations/v1/001.sql", True),
    ("**/assets/**/*.png", "assets/logo.png", True),
    ("**/assets/**/*.png", "x/assets/img/icons/a.png", True),
    ("packages/*/**/dist/*.js", "packages/core/dist/index.js", True),
    ("packages/*/**/dist/*.js", "packages/ui/x/y/dist/app.js", True),
    ("**/pkg/*/*/index.*", "pkg/a/b/index.js", True),
    ("**/pkg/*/*/index.*", "x/y/pkg/z/t/index.html", True),
    ("**/file*.py", "fileA.py", True),
    ("**/file*.py", "file.py", False),
    ("**/file**.py", "file.py", True),
    ("**/file**.py", "x/fileA.py", True),
    ("**/*test*.py", "x/y/unittest_tools.py", True),
    ("**/*test*.py", "test_main.py", False),
    ("*/*/folder/*/another.py", "a/b/folder/c/another.py", True),
    ("*/*/folder/*/another.py", "a/b/folder/c/d/another.py", False),
    ("*/*/folder/**/another.py", "a/b/folder/another.py", True),
    ("*/*/folder/**/another.py", "a/b/folder/x/y/another.py", True),
    ("*/*/folder/*/*/another.py", "a/b/folder/x/y/another.py", True),
    ("**/folder/***/file.txt", "folder/***/file.txt", True),
    ("**/folder/***/file.txt", "folder/x/file.txt", False),
    ("folder/*/file.txt", "folder/a/file.txt", True),
    ("folder/*/file.txt", "folder/a/b/file.txt", False),
    ("folder/**/file.txt", "folder/file.txt", True),
    ("folder/**/file.txt", "folder/a/b/file.txt", True),
    # file patterns with segment globs in directory part
    ("**/*hello/**/target.c", "abc/myhello/target.c", True),
    ("**/*hello/**/target.c", "abc/hello/target.c", False),
    ("**/**hello/**/target.c", "abc/hello/target.c", True),
    ("**/**hello/**/target.c", "abc/myhello/target.c", True),
    ("**/pre*fix/**/out.dat", "abc/preXYZfix/out.dat", True),
    ("**/pre*fix/**/out.dat", "abc/prefix/out.dat", False),
]


@pytest.mark.parametrize("pattern,filepath,expected", README_FILE_PATTERNS)
def test_readme_file_pattern_table(pattern: str, filepath: str, expected: bool):
    assert match_file(filepath, [pattern]) is expected


# ---------------------------------------------------------------------------
# Regressions (bugs found during development)
# ---------------------------------------------------------------------------

REGRESSION_FILE_CASES = [
    ("file.txt", ["file.txt"], True),
    ("x/file.txt", ["file.txt"], False),
    ("main.py", ["*.py"], True),
    ("src/app.py", ["*.py"], False),
    ("any/deep/file.dat", ["**"], True),
    ("README", ["README.**"], True),
    ("pkg/LICENSE", ["**/LICENSE**"], True),
    # **/migrations/* must match only one level under migrations (not deeper)
    ("app/migrations/001.sql", ["**/migrations/*"], True),
    ("app/migrations/v1/001.sql", ["**/migrations/*"], False),
    ("app/migrations/v1/001.sql", ["**/migrations/*/*"], True),
]


@pytest.mark.parametrize("path,patterns,expected", REGRESSION_FILE_CASES)
def test_regression_file_matching(path: str, patterns: list[str], expected: bool):
    assert match_file(path, patterns) is expected


# ---------------------------------------------------------------------------
# Specificity / precedence integration
# ---------------------------------------------------------------------------

SPECIFICITY_SCENARIOS = [
    pytest.param(
        ["**"],
        ["**/KLM/ABC/**"],
        ["**/KLM/**"],
        {
            "src/foo.py": True,
            "src/KLM/skip.py": False,
            "src/KLM/ABC/keep.py": True,
            "src/x/KLM/ABC/deep/keep.py": True,
        },
        id="klm-abc-exception",
    ),
    pytest.param(
        ["src/**"],
        ["**/ABC/KLM/**"],
        ["**/ABC/**"],
        {
            "src/foo.py": True,
            "src/ABC/only.py": False,
            "src/ABC/other/skip.py": False,
            "src/ABC/KLM/keep.py": True,
            "src/x/ABC/KLM/keep.py": True,
        },
        id="abc-klm-exception",
    ),
    pytest.param(
        ["**"],
        [],
        ["**/__pycache__/**"],
        {
            "src/app.py": True,
            "src/__pycache__/cached.py": False,
        },
        id="pycache-broad-exclude-wins",
    ),
    pytest.param(
        ["**"],
        [],
        ["**/skip/**"],
        {
            "skip/only.py": False,
            "keep/only.py": True,
            "other/only.py": True,
        },
        id="unrelated-exclude-does-not-block",
    ),
]


@pytest.mark.parametrize("inc_dirs,inc_odirs,exc_dirs,files", SPECIFICITY_SCENARIOS)
def test_specificity_integration(
    tmp_path: Path,
    inc_dirs: list[str],
    inc_odirs: list[str],
    exc_dirs: list[str],
    files: dict[str, bool],
):
    for rel in files:
        touch(tmp_path / rel)
    cfg = make_config(
        include_dirs=inc_dirs,
        include_odirs=inc_odirs,
        include_extensions=["py"],
        exclude_dirs=exc_dirs,
    )
    got = select_paths(tmp_path, cfg)
    for rel, should_include in files.items():
        assert (str(tmp_path / rel) in got) is should_include, rel


# ---------------------------------------------------------------------------
# Segment-glob exclude integration (end-to-end)
# ---------------------------------------------------------------------------

SEGMENT_EXCLUDE_SCENARIOS = [
    pytest.param(
        ["**/*hello/**"],
        {
            "ok/file.c": True,
            "ABC/Myhello/EFG/skip.c": False,
            "ABC/xhello/skip.c": False,
            "ABC/hello/EFG/keep.c": True,
        },
        id="star-hello-suffix",
    ),
    pytest.param(
        ["**/**hello/**"],
        {
            "ok/file.c": True,
            "ABC/hello/EFG/skip.c": False,
            "ABC/Myhello/EFG/skip.c": False,
            "ABC/other/keep.c": True,
        },
        id="doublestar-hello-suffix",
    ),
    pytest.param(
        ["**/hello*/**"],
        {
            "ABC/helloworld/x/skip.c": False,
            "ABC/hello/x/keep.c": True,
            "ABC/myhello/x/keep.c": True,
        },
        id="hello-prefix-glob",
    ),
    pytest.param(
        ["**/*abc*/**"],
        {
            "data/xabcy/nested/skip.c": False,
            "data/abc/keep.c": True,
            "data/ab/keep.c": True,
        },
        id="infix-abc-glob",
    ),
]


@pytest.mark.parametrize("exclude_dirs,files", SEGMENT_EXCLUDE_SCENARIOS)
def test_segment_glob_exclude_integration(
    tmp_path: Path,
    exclude_dirs: list[str],
    files: dict[str, bool],
):
    for rel in files:
        touch(tmp_path / rel)
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["c"],
        exclude_dirs=exclude_dirs,
    )
    got = select_paths(tmp_path, cfg)
    for rel, should_include in files.items():
        assert (str(tmp_path / rel) in got) is should_include, rel


# ---------------------------------------------------------------------------
# Multi-pattern OR semantics
# ---------------------------------------------------------------------------

def test_multiple_include_file_patterns_or(tmp_path: Path):
    touch(tmp_path / "a.py")
    touch(tmp_path / "b.js")
    touch(tmp_path / "c.txt")
    cfg = make_config(include_files=["**/*.py", "**/*.js"])
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "a.py") in paths
    assert str(tmp_path / "b.js") in paths
    assert str(tmp_path / "c.txt") not in paths


def test_multiple_exclude_dir_patterns_or(tmp_path: Path):
    touch(tmp_path / "ok/file.c")
    touch(tmp_path / "build/out.c")
    touch(tmp_path / "tmp/out.c")
    touch(tmp_path / "src/out.c")
    cfg = make_config(
        include_dirs=["**"],
        include_extensions=["c"],
        exclude_dirs=["**/build/**", "**/tmp/**"],
    )
    paths = select_paths(tmp_path, cfg)
    assert str(tmp_path / "ok/file.c") in paths
    assert str(tmp_path / "src/out.c") in paths
    assert str(tmp_path / "build/out.c") not in paths
    assert str(tmp_path / "tmp/out.c") not in paths


# ---------------------------------------------------------------------------
# Extension + path filter combinations
# ---------------------------------------------------------------------------

EXTENSION_COMBO_CASES = [
    pytest.param(["py"], [], "main.py", True, id="ext-match"),
    pytest.param(["py"], [], "main.md", False, id="ext-mismatch"),
    pytest.param(["tar.gz"], [], "archive.tar.gz", True, id="compound-ext"),
    pytest.param(["tar.gz"], [], "archive.tar", False, id="compound-ext-partial"),
    pytest.param([".*"], [], "dotted.txt", True, id="dot-star"),
    pytest.param([".*"], [], "noext", False, id="dot-star-no-ext"),
    pytest.param([], [".log"], "app.log", False, id="exclude-ext"),
    pytest.param([], [".log"], "app.py", True, id="exclude-ext-other"),
]


@pytest.mark.parametrize(
    "inc_ext,exc_ext,rel,expected", EXTENSION_COMBO_CASES
)
def test_extension_combinations(
    tmp_path: Path,
    inc_ext: list[str],
    exc_ext: list[str],
    rel: str,
    expected: bool,
):
    touch(tmp_path / rel)
    cfg = make_config(
        include_extensions=inc_ext or None,
        exclude_extensions=exc_ext or None,
    )
    paths = select_paths(tmp_path, cfg)
    assert (str(tmp_path / rel) in paths) is expected


# ---------------------------------------------------------------------------
# Case insensitivity across path, pattern, and extensions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pattern,dirpath",
    [
        ("**/myfolder/**", "abc/myfolder/sub"),
        ("**/*hello/**", "abc/xhello/efg"),
        ("folder/**/sub", "folder/a/sub"),
    ],
)
def test_case_insensitivity_dir_patterns(pattern: str, dirpath: str):
    assert match_dir(dirpath, [pattern.upper()]) is True


def test_case_insensitivity_file_pattern():
    assert match_file("src/MODULE.PY", ["**/*.PY"]) is True


def test_case_insensitive_full_pipeline(tree: Path):
    touch(tree / "SRC" / "MODULE.PY")
    cfg = make_config(include_extensions=["PY"], include_dirs=["**/src/**"])
    paths = select_paths(tree, cfg)
    assert str(tree / "SRC" / "MODULE.PY") in paths


# ---------------------------------------------------------------------------
# Depth / anchoring edge cases
# ---------------------------------------------------------------------------

DEPTH_CASES = [
    ("folder", "folder", True),
    ("folder", "a/folder", False),
    ("folder/*", "folder/a", True),
    ("folder/*", "a/folder/x", False),
    ("folder/*/*", "folder/a/b", True),
    ("folder/*/*", "folder/a", False),
    ("*/*/x", "a/b/x", True),
    ("*/*/x", "a/x", False),
    ("*/*/*/x", "a/b/c/x", True),
    ("*/*/*/x", "a/b/x", False),
]


@pytest.mark.parametrize("pattern,dirpath,expected", DEPTH_CASES)
def test_dir_depth_anchoring(pattern: str, dirpath: str, expected: bool):
    assert match_dir(dirpath, [pattern]) is expected


# ---------------------------------------------------------------------------
# matches() API consistency with select()
# ---------------------------------------------------------------------------

def test_matches_agrees_with_select(tmp_path: Path):
    from conftest import rules_for
    import json
    from filefilter import load

    files = {
        "a.py": True,
        "build/a.py": False,
        "src/b.py": True,
    }
    for rel in files:
        touch(tmp_path / rel)
    cfg = make_config(
        include_dirs=["src/**", "*.py"],
        include_extensions=["py"],
        exclude_dirs=["build"],
    )
    rules = rules_for(tmp_path, cfg)
    selected = select_paths(tmp_path, cfg)
    for rel, _ in files.items():
        full = str(tmp_path / rel)
        assert matches(full, rules) == (full in selected or str(tmp_path / rel) in selected)


# ---------------------------------------------------------------------------
# Empty / degenerate inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pattern,path",
    [
        ("", "a/b"),
        ("**", ""),
    ],
)
def test_degenerate_dir_patterns_do_not_crash(pattern: str, path: str):
    assert match_dir(path, [pattern]) in (True, False)


@pytest.mark.parametrize(
    "pattern,path",
    [
        ("", "file.txt"),
        ("**", "a/b/c"),
    ],
)
def test_degenerate_file_patterns_do_not_crash(pattern: str, path: str):
    assert match_file(path, [pattern]) in (True, False)
