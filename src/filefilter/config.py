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

"""Parse filefilter configuration from JSON, YAML, or TOML text or files."""

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

import json
import os
import re

import yaml

#########################################################################################
#########################################################################################

_FORMAT_BY_SUFFIX = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
}

# Plain scalars stay strings. PyYAML would otherwise rewrite patterns such as
# "01", "on", "yes", or "null" into ints, bools, or None.
class _YamlLoader(yaml.SafeLoader):
    pass


_YamlLoader.yaml_implicit_resolvers = {}

_TOML_BARE = r"[A-Za-z0-9_-]+"
_TOML_QUOTED = r"(?:\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*')"
_TOML_KEY = (
    rf"(?:{_TOML_BARE}|{_TOML_QUOTED})"
    rf"(?:\s*\.\s*(?:{_TOML_BARE}|{_TOML_QUOTED}))*"
)
_TOML_KV_RE = re.compile(rf"^{_TOML_KEY}\s*=")
_TOML_TABLE_RE = re.compile(rf"^\[\[?\s*{_TOML_KEY}\s*\]\]?\s*(?:#.*)?$")

#########################################################################################

def _load_toml(text):
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # pragma: no cover
    return tomllib.loads(text)

#########################################################################################

def _prepare(text):
    if text.startswith("\ufeff"):
        text = text[1:]
    return text

#########################################################################################

def _require_mapping(data, label):
    if isinstance(data, dict):
        return data
    kind = "empty" if data is None else type(data).__name__
    raise ValueError(f"{label} configuration must be a mapping, got {kind}")

#########################################################################################

def _first_content_line(text):
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped in ("---", "..."):
            continue
        return stripped
    return ""

#########################################################################################

def _looks_like_toml(text):
    line = _first_content_line(text)
    if not line:
        return False
    if _TOML_TABLE_RE.match(line) or _TOML_KV_RE.match(line):
        return True
    return False

#########################################################################################

def _looks_like_inline(text):
    return any(ch in text for ch in "{}=:#[]")

#########################################################################################

def _parse_yaml(text):
    try:
        data = yaml.load(text, Loader=_YamlLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML configuration: {exc}") from exc
    return _require_mapping(data, "YAML")

#########################################################################################

def _parse_format(text, fmt):
    if not text.strip():
        raise ValueError("configuration is empty")
    if fmt == "json":
        return _require_mapping(json.loads(text), "JSON")
    if fmt == "yaml":
        return _parse_yaml(text)
    return _require_mapping(_load_toml(text), "TOML")

#########################################################################################

def _parse_autodetect(text):
    if not text.strip():
        raise ValueError("configuration is empty")

    stripped = text.strip()
    errors = []
    json_error = None
    if stripped[:1] in "{[":
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            json_error = exc
            errors.append(f"JSON: {exc}")
        else:
            return _require_mapping(data, "JSON")

    attempts = ("TOML", "YAML") if _looks_like_toml(stripped) else ("YAML", "TOML")
    for label in attempts:
        try:
            if label == "TOML":
                data = _load_toml(stripped)
            else:
                data = yaml.load(stripped, Loader=_YamlLoader)
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f"{label}: {exc}")
            continue
        if isinstance(data, dict):
            return data
        if data is None:
            raise ValueError("configuration is empty")
        errors.append(
            f"{label}: configuration must be a mapping, got {type(data).__name__}"
        )

    if json_error is not None:
        raise json_error
    raise ValueError(
        "could not parse configuration as JSON, YAML, or TOML:\n" + "\n".join(errors)
    )

#########################################################################################

def _read_source(config):
    """Return ``(text, format)``. ``format`` is set when ``config`` is a file path."""
    if isinstance(config, os.PathLike):
        config = os.fspath(config)
    if not isinstance(config, str):
        raise TypeError(
            "config must be JSON, YAML, or TOML text, or a path to a "
            ".json, .yaml, .yml, or .toml file"
        )

    config = _prepare(config)
    if any(ch in config for ch in "\r\n"):
        return config, None

    candidate = config.strip()
    suffix = os.path.splitext(candidate)[1].lower()
    fmt = _FORMAT_BY_SUFFIX.get(suffix)
    if fmt is None:
        return config, None
    if os.path.isdir(candidate):
        raise IsADirectoryError(candidate)
    if os.path.isfile(candidate):
        with open(candidate, encoding="utf-8-sig") as handle:
            return handle.read(), fmt
    if not _looks_like_inline(candidate):
        raise FileNotFoundError(candidate)
    return config, None

#########################################################################################

def parse_config(config):
    """Parse configuration text or a config file into a mapping."""
    text, fmt = _read_source(config)
    if fmt is None:
        return _parse_autodetect(text)
    return _parse_format(text, fmt)

#########################################################################################
#########################################################################################
