from __future__ import annotations

import pytest

from filefilter.utilities import (
    count_leading_stars,
    match_doublestar_segments,
    matching_extensions,
    matching_patterns,
    merge_dir_patterns,
    normalize_path,
    parse_dir_patterns,
    parse_extensions,
    segment_matches,
    split_path,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Foo/Bar", "foo/bar"),
        ("Foo\\Bar\\Baz", "foo/bar/baz"),
        ("  /leading/  ", "/leading/"),
        ("//double//slash//", "/double/slash/"),
    ],
)
def test_normalize_path(raw: str, expected: str):
    assert normalize_path(raw) == expected


def test_split_path_drops_empty_segments():
    assert split_path("/a//b/") == ["a", "b"]


@pytest.mark.parametrize(
    "pattern,stars,tail",
    [
        ("*/a/b", 1, "a/b"),
        ("*/*/a", 2, "a"),
        ("**/tail", -1, "tail"),
        ("plain/tail", 0, "plain/tail"),
    ],
)
def test_count_leading_stars(pattern: str, stars: int, tail: str):
    assert count_leading_stars(pattern) == (stars, tail)


def test_match_doublestar_segments_middle_gap():
    parts = ["a", "b", "c", "d"]
    ends = match_doublestar_segments(parts, 0, ["a", "**", "d"])
    assert ends == [4]


def test_match_doublestar_single_segment_wildcard():
    parts = ["folder", "x", "y"]
    ends = match_doublestar_segments(parts, 0, ["folder", "*", "y"])
    assert 3 in ends
    assert 2 not in ends


@pytest.mark.parametrize(
    "token,part,expected",
    [
        ("*hello", "myhello", True),
        ("*hello", "hello", False),
        ("*hello", "xhello", True),
        ("**hello", "hello", True),
        ("**hello", "myhello", True),
        ("**hello", "xhello", True),
        ("hello*", "helloworld", True),
        ("hello*", "hello", False),
        ("hello**", "hello", True),
        ("hello**", "helloworld", True),
        ("abc*", "abcx", True),
        ("abc*", "abc", False),
        ("*abc", "xabc", True),
        ("*abc", "abc", False),
        ("*abc*", "xabcy", True),
        ("*abc*", "abc", False),
        ("folder", "folder", True),
        ("folder", "other", False),
        ("***", "***", True),
        ("***", "myhello", False),
    ],
)
def test_segment_matches_glob(token: str, part: str, expected: bool):
    assert segment_matches(token, part) is expected


def test_match_doublestar_segments_glob_in_segment():
    parts = ["abc", "myhello", "efg"]
    assert match_doublestar_segments(parts, 1, ["*hello"]) == [2]
    assert match_doublestar_segments(parts, 0, ["abc", "*hello"]) == [2]
    assert match_doublestar_segments(parts, 0, ["**", "*hello"]) == [2]
    parts2 = ["abc", "helloworld", "efg"]
    assert match_doublestar_segments(parts2, 1, ["hello*"]) == [2]
    assert match_doublestar_segments(parts2, 0, ["abc", "hello*"]) == [2]


def test_parse_dir_patterns_buckets():
    root, one, any_ = parse_dir_patterns(
        ["src", "*/pkg", "**/cache", "/", "  "]
    )
    assert root == ["src"]
    assert one == ["*/pkg"]
    assert any_ == ["**/cache"]


def test_merge_dir_patterns_flattens_buckets():
    merged = merge_dir_patterns(["src", "*/pkg", "**/cache"])
    assert merged == ["src", "*/pkg", "**/cache"]


def test_parse_extensions_strips_and_dots():
    assert parse_extensions(["PY", ".md", "tar.gz", "", ".*"]) == [
        ".py",
        ".md",
        ".tar.gz",
        ".*",
    ]


def test_matching_extensions_compound_suffix_by_filename():
    assert matching_extensions(".gz", [".tar.gz"], "archive.tar.gz") == [".tar.gz"]
    assert matching_extensions(".gz", [".tar.gz"], "archive.gz") == []


def test_matching_extensions_dot_star_requires_non_empty_extension():
    assert matching_extensions("", [".*"], "noext") == []
    assert matching_extensions(".py", [".*"], "main.py") == [".*"]


def test_matching_extensions_fnmatch_single_component():
    assert matching_extensions(".py", [".py"], "main.py") == [".py"]
    assert matching_extensions(".pyc", [".py"], "main.pyc") == []


def test_matching_extensions_via_fnmatch_when_endswith_does_not():
    assert matching_extensions(".py", [".p?"], "main.py") == [".p?"]


@pytest.mark.parametrize(
    "filepath,patterns,expected",
    [
        ("", ["**"], False),
        ("/", ["**"], False),
        ("x/file.txt", ["*"], False),
        ("file.txt", ["*/file.txt"], False),
        ("a/file.txt", ["*/*/subdir/file.txt"], False),
        ("a/file.txt", ["*/file.txt"], True),
    ],
)
def test_match_file_edge_cases(filepath: str, patterns: list[str], expected: bool):
    from filefilter import match_file

    assert match_file(filepath, patterns) is expected


def test_matching_patterns_returns_all_hits():
    from filefilter import match_file

    got = matching_patterns(["*.py", "**/*.py", "readme.md"], match_file, "src/app.py")
    assert got == ["**/*.py"]


def test_matching_extensions_returns_all_hits():
    assert matching_extensions(".py", [".py", ".*"], "app.py") == [".py", ".*"]
    assert matching_extensions("", [".py", ".*"], "readme") == []
    assert matching_extensions(".tar.gz", [".tar.gz"], "archive.tar.gz") == [".tar.gz"]
    assert matching_extensions(".py", [".p*"], "app.py") == [".p*"]
