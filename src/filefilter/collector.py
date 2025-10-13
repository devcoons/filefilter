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
from .utilities import *
from .ruleset import *

#########################################################################################
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
            continue 

        pat_filename = tail_parts[-1]
        pat_dirs = tail_parts[:-1]
        rx = re.escape(pat_filename)
        rx = rx.replace(r'\*\*', '.*') 
        rx = rx.replace(r'\*',  '.+')  
        if not re.match(r'^' + rx + r'$', filename):
            continue

        if lead_stars == -1:               
            start_positions = range(0, depth + 1)
            if not pat_dirs:
                return True 
            for s in start_positions:
                ends = match_doublestar_segments(dir_parts, s, pat_dirs)
                if ends:                   
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
    """Decide inclusion using match_file/match_dir with include/exclude/extension rules."""
    rel = normalize_path(os.path.relpath(full_path, cfg.root_dir))
    segments = rel.split('/')
    name = segments[-1]
    dir_rel = '/'.join(segments[:-1])
    _, ext = os.path.splitext(name)

    def _merge(*lists):
        out = []
        for lst in lists:
            if lst:
                out.extend(lst)
        return out

    if cfg.exc_exts and ext_matches(ext, cfg.exc_exts):
        return False
    if cfg.exclude_files and match_file(rel, cfg.exclude_files):
        return False
    exc_dirs = _merge(cfg.exc_dirs_root, cfg.exc_dirs_one, cfg.exc_dirs_any)
    if exc_dirs and match_dir(dir_rel, exc_dirs):
        return False
    files_present = bool(cfg.include_files)
    files_match = files_present and match_file(rel, cfg.include_files)
    if files_match:
        return True
    inc_dirs = _merge(cfg.inc_dirs_root, cfg.inc_dirs_one, cfg.inc_dirs_any)
    dirs_present = bool(inc_dirs)
    dirs_match = dirs_present and match_dir(dir_rel, inc_dirs)
    if (files_present or dirs_present) and not (files_match or dirs_match):
        return False 
    if cfg.inc_exts and not ext_matches(ext, cfg.inc_exts):
        return False
    return True

#########################################################################################

def collect_files(cfg: Ruleset) -> list:
    """Walk root_dir and collect files passing should_include."""
    matches = []
    for root, _, files in os.walk(cfg.root_dir, followlinks=False):
        for fn in files:
            full = os.path.join(root, fn)
            if os.path.islink(full):
                continue
            if should_include(full, cfg):
                matches.append(os.path.normpath(full))
    return matches

#########################################################################################
#########################################################################################

