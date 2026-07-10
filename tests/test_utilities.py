from __future__ import annotations

import pytest

from filefilter.utilities import (
    best_matching_specificity,
    count_leading_stars,
    ext_matches,
    match_doublestar_segments,
    normalize_path,
    parse_dir_patterns,
    parse_extensions,
    pattern_specificity,
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


def test_parse_dir_patterns_buckets():
    root, one, any_ = parse_dir_patterns(
        ["src", "*/pkg", "**/cache", "/", "  "]
    )
    assert root == ["src"]
    assert one == ["*/pkg"]
    assert any_ == ["**/cache"]


def test_parse_extensions_strips_and_dots():
    assert parse_extensions(["PY", ".md", "tar.gz", "", ".*"]) == [
        ".py",
        ".md",
        ".tar.gz",
        ".*",
    ]


def test_ext_matches_compound_suffix_by_filename():
    assert ext_matches(".gz", [".tar.gz"], "archive.tar.gz") is True
    assert ext_matches(".gz", [".tar.gz"], "archive.gz") is False


def test_ext_matches_dot_star_requires_non_empty_extension():
    assert ext_matches("", [".*"], "noext") is False
    assert ext_matches(".py", [".*"], "main.py") is True


def test_ext_matches_fnmatch_single_component():
    assert ext_matches(".py", [".py"], "main.py") is True
    assert ext_matches(".pyc", [".py"], "main.pyc") is False


def test_ext_matches_via_fnmatch_when_endswith_does_not():
    assert ext_matches(".py", [".p?"], "main.py") is True


def test_pattern_specificity_skips_empty_segments():
    assert pattern_specificity("/foo") == pattern_specificity("foo")


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


def test_best_matching_specificity_no_match():
    from filefilter import match_dir

    assert best_matching_specificity(["folder"], match_dir, "other") == -1


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("**/KLM/ABC/**", "**/KLM/**", True),
        ("**", "**/KLM/**", False),
        ("src/**", "src/KLM/**", False),
        ("**/ABC/KLM/**", "**/ABC/**", True),
    ],
)
def test_pattern_specificity_ordering(a: str, b: str, expected: bool):
    assert (pattern_specificity(a) > pattern_specificity(b)) is expected
