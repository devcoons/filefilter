#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy          #
# of this software and associated documentation files (the "Software"), to deal         #
# in the Software without restriction, including without limitation the rights          #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell             #
# copies of the Software, and to permit persons to whom the Software is                 #
# furnished to do so, subject to the following conditions:                              #
#                                                                                       #
# The above copyright notice and this permission notice shall be included in all        #
# copies or substantial portions of the Software.                                       #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR            #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,              #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE           #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,         #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE         #
# SOFTWARE.                                                                             #
#                                                                                       #
#########################################################################################

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

import os
from dataclasses import dataclass, field
from .utilities import *
from .ruleset import *

#########################################################################################
#########################################################################################

def _matches(matcher, target: str, patterns: list[str]) -> bool:
    return bool(patterns and matcher(target, patterns))


def _file_context(full_path: str, root_dir: str) -> tuple[str, str, str, str]:
    rel = normalize_path(os.path.relpath(full_path, root_dir))
    segments = rel.split('/')
    name = segments[-1]
    dir_rel = '/'.join(segments[:-1])
    _, ext = os.path.splitext(name)
    return rel, dir_rel, name, ext

#########################################################################################

@dataclass
class DryRunResult:
    """Outcome of a dry-run scan: selected files and per-rule hit counts."""
    scanned: int = 0
    included: list[str] = field(default_factory=list)
    hits: dict[str, int] = field(default_factory=dict)

    @property
    def excluded(self) -> int:
        return self.scanned - len(self.included)

    def count(self, rule: str) -> int:
        """How many files matched this rule key (0 if never hit)."""
        return self.hits.get(rule, 0)

    def was_hit(self, rule: str) -> bool:
        """True if this rule matched at least one file."""
        return self.count(rule) > 0

    def has_rule(self, rule: str) -> bool:
        """True if this rule was configured (appears in hits, possibly with count 0)."""
        return rule in self.hits

    def _record(self, category: str, patterns: list[str], n: int = 1) -> None:
        for patt in patterns:
            key = f"{category}:{patt}"
            self.hits[key] = self.hits.get(key, 0) + n

    def _seed_extensions(self, cfg: Ruleset) -> None:
        for category, patterns in (
            ("include.extensions", cfg.inc_exts),
            ("exclude.extensions", cfg.exc_exts),
        ):
            for patt in patterns or []:
                self.hits.setdefault(f"{category}:{patt}", 0)

#########################################################################################

def match_dir(dirpath: str, include_dirs: list[str]) -> bool:
    """Return True if directory path matches any include_dir pattern (supports /**/ in the middle)."""
    parts = split_path(dirpath.rstrip('/'))
    depth = len(parts)

    for raw in include_dirs:
        patt = normalize_path(raw).rstrip('/')
        suffix_mode = 'exact'
        if patt.endswith('/**'):
            patt = patt[:-3]
            suffix_mode = 'deep'
        else:
            m = re.search(r'(?:/\*)+$', patt)
            if m:
                stars = m.group(0)
                patt = patt[: -len(stars)]
                n_after = stars.count('/*')
                suffix_mode = f"exactly_{n_after}"

        lead_stars, tail = count_leading_stars(patt)
        tail_parts = split_path(tail)

        if lead_stars == -1 and suffix_mode == 'deep' and not tail_parts:
            return True
        if lead_stars == -1:                          
            start_positions = range(0, depth + 1)
        elif lead_stars == 0:                        
            start_positions = range(0, 1)
        else:                                      
            if depth < lead_stars:
                continue
            start_positions = range(lead_stars, lead_stars + 1)

        for s in start_positions:
            ends = match_doublestar_segments(parts, s, tail_parts)
            if not ends:
                continue
            for e in ends:
                remain = depth - e
                if suffix_mode == 'exact' and remain == 0:
                    return True
                if suffix_mode == 'deep':
                    return True
                if suffix_mode.startswith('exactly_'):
                    n = int(suffix_mode.split('_')[1])
                    if remain == n:
                        return True
    return False

#########################################################################################

def match_file(filepath: str, include_files: list[str]) -> bool:
    """Return True if file path matches any include_file pattern. """
    parts = split_path(filepath)
    if not parts:
        return False

    dir_parts = parts[:-1]
    filename = parts[-1]
    depth = len(dir_parts)

    for raw in include_files or []:
        patt = normalize_path(raw)
        lead_stars, tail = count_leading_stars(patt)
        tail_parts = split_path(tail)
        if not tail_parts:
            if lead_stars == -1:
                return True
            continue

        pat_filename = tail_parts[-1]
        pat_dirs = tail_parts[:-1]
        rx = re.escape(pat_filename)
        rx = rx.replace(r'\.\*\*', r'(\..*)?')
        rx = rx.replace(r'\*\*', '.*')
        rx = rx.replace(r'\*',  '.+')
        if not re.match(r'^' + rx + r'$', filename):
            continue

        if not pat_dirs:
            if lead_stars == -1:
                return True
            if lead_stars == 0 and depth == 0:
                return True
            if lead_stars > 0 and depth == lead_stars:
                return True
            continue

        if lead_stars == -1:
            start_positions = range(0, depth + 1)
            for s in start_positions:
                ends = match_doublestar_segments(dir_parts, s, pat_dirs)
                if any(e == depth for e in ends):
                    return True
        elif lead_stars == 0:               
            s = 0
            ends = match_doublestar_segments(dir_parts, s, pat_dirs)
            if any(e == depth for e in ends) if pat_dirs else (depth == 0):
                return True
        else:                             
            if depth < lead_stars:
                continue
            s = lead_stars
            ends = match_doublestar_segments(dir_parts, s, pat_dirs)
            if any(e == depth for e in ends) if pat_dirs else (depth == lead_stars):
                return True
    return False

#########################################################################################

def should_include(full_path: str, cfg: Ruleset) -> bool:
    """Decide inclusion: scope (include) -> exclude -> override (odirs/ofiles) -> extensions."""
    rel, dir_rel, name, ext = _file_context(full_path, cfg.root_dir)
    include_files = cfg.include_files or []
    ofiles = cfg.include_ofiles or []

    if cfg.exc_exts and matching_extensions(ext, cfg.exc_exts, name):
        return False

    if (cfg.inc_dirs or include_files) and not (
        _matches(match_file, rel, include_files) or _matches(match_dir, dir_rel, cfg.inc_dirs)
    ):
        return False

    excluded = (
        _matches(match_file, rel, cfg.exclude_files)
        or _matches(match_dir, dir_rel, cfg.exc_dirs)
    )
    if excluded and not (
        _matches(match_dir, dir_rel, cfg.inc_odirs)
        or _matches(match_file, rel, ofiles)
    ):
        return False

    if _matches(match_file, rel, include_files):
        return True
    if cfg.inc_exts and not matching_extensions(ext, cfg.inc_exts, name):
        return False
    return True


def _extension_pass_applies(rel: str, dir_rel: str, name: str, ext: str, cfg: Ruleset) -> bool:
    """True when should_include would evaluate include.extensions for this path."""
    if not cfg.inc_exts:
        return False
    include_files = cfg.include_files or []
    ofiles = cfg.include_ofiles or []
    if cfg.exc_exts and matching_extensions(ext, cfg.exc_exts, name):
        return False
    if (cfg.inc_dirs or include_files) and not (
        _matches(match_file, rel, include_files) or _matches(match_dir, dir_rel, cfg.inc_dirs)
    ):
        return False
    excluded = (
        _matches(match_file, rel, cfg.exclude_files)
        or _matches(match_dir, dir_rel, cfg.exc_dirs)
    )
    if excluded and not (
        _matches(match_dir, dir_rel, cfg.inc_odirs)
        or _matches(match_file, rel, ofiles)
    ):
        return False
    return not _matches(match_file, rel, include_files)

#########################################################################################

def _iter_candidate_files(cfg: Ruleset):
    """Yield non-symlink files under cfg.root_dir."""
    for root, _, files in os.walk(cfg.root_dir, followlinks=False):
        for fn in files:
            full = os.path.join(root, fn)
            if not os.path.islink(full):
                yield full

#########################################################################################

def scan(cfg: Ruleset) -> list[str]:
    """Walk root_dir and return files accepted by the rules."""
    return [
        os.path.normpath(full)
        for full in _iter_candidate_files(cfg)
        if should_include(full, cfg)
    ]

#########################################################################################

def matches(path: str, cfg: Ruleset) -> bool:
    """Return True if `path` would be included by `cfg`."""
    return should_include(path, cfg)

#########################################################################################

_RULE_GROUPS = (
    ("include.dirs", "inc_dirs", "dir"),
    ("include.odirs", "inc_odirs", "dir"),
    ("include.files", "include_files", "file"),
    ("include.ofiles", "include_ofiles", "file"),
    ("exclude.dirs", "exc_dirs", "dir"),
    ("exclude.files", "exclude_files", "file"),
)

#########################################################################################

def dry_run(cfg: Ruleset) -> DryRunResult:
    """Walk root_dir without side effects; return selections and per-rule hit counts."""
    result = DryRunResult()
    result._seed_extensions(cfg)

    for full in _iter_candidate_files(cfg):
        result.scanned += 1
        rel, dir_rel, name, ext = _file_context(full, cfg.root_dir)

        for category, attr, kind in _RULE_GROUPS:
            patterns = getattr(cfg, attr) or []
            target = dir_rel if kind == "dir" else rel
            matcher = match_dir if kind == "dir" else match_file
            result._record(category, matching_patterns(patterns, matcher, target))

        result._record(
            "exclude.extensions",
            matching_extensions(ext, cfg.exc_exts, name),
        )
        if _extension_pass_applies(rel, dir_rel, name, ext, cfg):
            result._record(
                "include.extensions",
                matching_extensions(ext, cfg.inc_exts, name),
            )

        if should_include(full, cfg):
            result.included.append(os.path.normpath(full))

    return result

#########################################################################################
#########################################################################################