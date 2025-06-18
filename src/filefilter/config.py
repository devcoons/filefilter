import os
import re
from fnmatch import fnmatch


def normalize_path(p: str) -> str:
    """
    Collapse backslashes and multiple slashes to '/', trim whitespace.
    """
    p = re.sub(r"[\\/]+", "/", p)
    return p.strip()


def parse_dir_patterns(patterns):
    """
    Parse directory glob patterns into:
      - root-only patterns (first segment match)
      - anywhere patterns (any ancestor segment)
    Strips '**/' prefix and '/**' suffix, handles leading '/' for root-only.
    """
    root_patts = []
    any_patts = []
    for raw in patterns:
        p = normalize_path(raw)
        low = p.lower()
        anchored = p.startswith("/")
        # remove recursive markers for internal logic
        low = re.sub(r"^\*\*/", "", low)
        low = re.sub(r"/\*\*$", "", low)
        low = low.rstrip("/")
        if not low:
            continue
        if anchored:
            root_patts.append(low)
        else:
            any_patts.append(low)
    return root_patts, any_patts


def parse_file_patterns(patterns):
    """
    Normalize and lowercase filename patterns (wildcards '*' only).
    """
    return [normalize_path(p).lower() for p in patterns]


def parse_extensions(patterns):
    """
    Normalize and lowercase extensions, ensure leading '.'.
    """
    out = []
    for e in patterns:
        norm = normalize_path(e).lower().lstrip('.')
        out.append('.' + norm)
    return out


class Config:
    def __init__(self, data: dict, resolve_base: str = ''):
        """
        Initialize configuration from a dict.

        Parameters:
          - data: parsed JSON dict containing 'root_dir' and 'filters'
          - resolve_base: 'cwd' or 'script'
        """
        raw_root = normalize_path(data['root_dir'])
        # Resolve absolute or relative root_dir
        if os.path.isabs(raw_root):
            root = raw_root
        else:
            if resolve_base == '':
                base_dir = os.getcwd()
                
            else:
                base_dir = normalize_path(resolve_base)
            root = os.path.join(base_dir, raw_root)
        self.root_dir = os.path.normpath(root)

        inc = data['filters']['include']
        exc = data['filters']['exclude']

        # Include/Exclude directory patterns
        self.inc_dirs_root, self.inc_dirs_any = parse_dir_patterns(inc.get('dirs', []))
        self.exc_dirs_root, self.exc_dirs_any = parse_dir_patterns(exc.get('dirs', []))

        # Include/Exclude filename patterns
        self.include_files = parse_file_patterns(inc.get('files', []))
        self.exclude_files = parse_file_patterns(exc.get('files', []))

        # Include/Exclude extensions
        self.inc_exts = parse_extensions(inc.get('extensions', []))
        self.exc_exts = parse_extensions(exc.get('extensions', []))