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

__version__ = '0.1.12'

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

import json
import warnings
from .utilities import *
from .ruleset import *
from .collector import *

__all__ = [
    # Preferred API
    "Ruleset", "load", "scan", "matches", "select", "match_dir", "match_file",
    # Legacy API (still supported)
    "filter_paths"
]
#########################################################################################

def _warn(old: str, new: str):
    warnings.warn(
        f"'filefilter.{old}' is deprecated and will be removed in 0.2.0; "
        f"use 'filescan.{new}'",
        DeprecationWarning,
        stacklevel=2,
    )

#########################################################################################

def load(config_json: str, base: str = "cwd") -> Ruleset:
    """
    Parse the config JSON and return a RuleSet resolved against `base`.
    Equivalent to: RuleSet(json.loads(config_json), resolve_base=base)
    """
    data = json.loads(config_json)
    return Ruleset(data, resolve_base=base)

#########################################################################################

def scan(rules: Ruleset) -> list[str]:
    """
    Walk rules.root_dir and return files accepted by the rules.
    Equivalent to: collect_files(rules)
    """
    return collect_files(rules)

#########################################################################################

def matches(path: str, rules: Ruleset) -> bool:
    """
    Return True if `path` would be included by `rules`.
    Equivalent to: should_include(path, rules)
    """
    return should_include(path, rules)

#########################################################################################

def select(config_json: str, base: str = "cwd") -> list[str]:
    """
    Convenience: load(...) + scan(...).
    """
    return scan(load(config_json, base=base))

#########################################################################################

def filter_paths(config_json: str, resolve_base: str = 'cwd'):
    """Load config JSON, build Config, and return collected files."""
    _warn("filter_paths", "select")
    data = json.loads(config_json)
    cfg = Ruleset(data, resolve_base=resolve_base)
    return collect_files(cfg)

#########################################################################################
#########################################################################################