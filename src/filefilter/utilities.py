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

import re
from fnmatch import fnmatch

#########################################################################################
#########################################################################################

def normalize_path(p: str) -> str:
    """Normalize and lowercase a path."""
    return re.sub(r"[\\/]+", "/", p.strip()).lower()

#########################################################################################

def parse_file_patterns(patterns):
    """Normalize and lowercase file patterns."""
    return [normalize_path(p) for p in (patterns or [])]

#########################################################################################

def split_path(path: str):
    """Split normalized path into segments."""
    path = normalize_path(path)
    parts = path.split('/')
    return [p for p in parts if p]

#########################################################################################

def parse_dir_patterns(patterns):
    """Bucket dir patterns by leading marker: root (none), one+ (*/...), or any (**/...)."""
    root_patts, one_patts, any_patts = [], [], []
    for raw in patterns or []:
        p = normalize_path(raw).rstrip('/')
        if not p:
            continue
        if p.startswith('**/'):
            any_patts.append(p)
        elif p.startswith('*/'):
            one_patts.append(p)
        else:
            root_patts.append(p)
    return root_patts, one_patts, any_patts

#########################################################################################

def parse_extensions(patterns):
    """Normalize and lowercase extensions, ensure leading '.'."""
    out = []
    for e in patterns or []:
        norm = normalize_path(e).lstrip('.')
        if norm:
            out.append('.' + norm)
    return out

#########################################################################################

def count_leading_stars(patt: str) -> tuple[int, str]:
    """Count leading */ or **/ markers and return remaining pattern."""
    p = normalize_path(patt)
    parts = p.split('/')
    n = 0
    for seg in parts:
        if seg == '*':
            n += 1
        elif seg == '**':
            return -1, '/'.join(parts[1:])
        else:
            break
    return n, '/'.join(parts[n:])

#########################################################################################

def match_doublestar_segments(path_parts: list[str], start: int, patt_parts: list[str]) -> list[int]:
    """Return a list of end indices j such that path_parts[start:j] matches patt_parts where '**' means zero+ segments."""
    results = []
    def rec(i: int, j: int):
        if i == len(patt_parts):
            results.append(j)
            return
        token = patt_parts[i]
        if token == '**':
            for k in range(j, len(path_parts) + 1):
                rec(i + 1, k)
        elif token == '*':
            if j < len(path_parts):
                rec(i + 1, j + 1)
        else:
            if j < len(path_parts) and path_parts[j] == token:
                rec(i + 1, j + 1)
    rec(0, start)
    return results

#########################################################################################

def ext_matches(ext: str, patterns: list[str]) -> bool:
    """True if ext matches any pattern; '.*' means any non-empty extension only."""
    for p in patterns or []:
        if p == '.*':
            if ext:
                return True
            continue
        if fnmatch(ext, p):
            return True
    return False

#########################################################################################
#########################################################################################
