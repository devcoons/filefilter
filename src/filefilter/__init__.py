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

__version__ = '0.2.6'

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

from .config import parse_config
from .ruleset import Filter, Ruleset
from .collector import (
    DryRunResult,
    dry_run,
    match_dir,
    match_file,
    matches,
    scan,
)

__all__ = [
    "Filter", "Ruleset", "load", "scan", "matches", "select", "dry_run",
    "DryRunResult", "match_dir", "match_file",
]

#########################################################################################

def _one_config(config, config_json, caller):
    if config is not None and config_json is not None:
        raise TypeError(f"{caller}() got both 'config' and 'config_json'")
    if config is None:
        config = config_json
    if config is None:
        raise TypeError(f"{caller}() missing required argument: 'config'")
    return config

#########################################################################################

def load(config=None, base: str = "cwd", *, config_json=None) -> Ruleset:
    """Parse JSON, YAML, or TOML configuration and return a Ruleset.

    `config` is the document text, or a path to a `.json`, `.yaml`, `.yml`,
    or `.toml` file. Format is taken from the file extension, otherwise
    detected from the text. Existing JSON strings keep their previous meaning.

    `base` resolves a relative `root_dir` (`"cwd"`, `"script"`, or a directory).
    `config_json` is a keyword alias of `config`.
    """
    source = _one_config(config, config_json, "load")
    return Ruleset(parse_config(source), resolve_base=base)

#########################################################################################

def select(config=None, base: str = "cwd", *, config_json=None) -> list[str]:
    """Convenience: load(...) + scan(...). Accepts the same config as `load`."""
    return scan(load(_one_config(config, config_json, "select"), base=base))

#########################################################################################
#########################################################################################
