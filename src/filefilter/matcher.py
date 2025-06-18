import os
from fnmatch import fnmatch
from .config import normalize_path, Config


def should_include(full_path: str, cfg: Config) -> bool:
    """
    Determine if a file should be included based on the config rules.
    """
    rel = os.path.relpath(full_path, cfg.root_dir)
    rel = normalize_path(rel).lower()
    segments = rel.split('/')
    name = segments[-1]
    ancestors = segments[:-1]
    _, ext = os.path.splitext(name)

    # 1) Include-files override
    for patt in cfg.include_files:
        if fnmatch(name, patt):
            return True

    # 2) Exclude by extension
    if ext in cfg.exc_exts:
        return False

    # 3) Exclude by filename
    for patt in cfg.exclude_files:
        if fnmatch(name, patt):
            return False

    # 4) Exclude by directory (root-only)
    if ancestors and cfg.exc_dirs_root:
        first = ancestors[0]
        for patt in cfg.exc_dirs_root:
            if fnmatch(first, patt):
                return False
    # Exclude by directory (anywhere)
    for seg in ancestors:
        for patt in cfg.exc_dirs_any:
            if fnmatch(seg, patt):
                return False

    # 5) Include by directory if patterns exist
    if cfg.inc_dirs_root or cfg.inc_dirs_any:
        ok = False
        if ancestors and cfg.inc_dirs_root:
            first = ancestors[0]
            for patt in cfg.inc_dirs_root:
                if fnmatch(first, patt):
                    ok = True
                    break
        if not ok and cfg.inc_dirs_any:
            for seg in ancestors:
                for patt in cfg.inc_dirs_any:
                    if fnmatch(seg, patt):
                        ok = True
                        break
                if ok:
                    break
        if not ok:
            return False

    # 6) Include by extension
    if cfg.inc_exts and ext not in cfg.inc_exts:
        return False

    return True


def collect_files(cfg: Config) -> list:
    """
    Walk root_dir and collect files passing should_include.
    """
    matches = []
    for root, _, files in os.walk(cfg.root_dir, followlinks=False):
        for fn in files:
            full = os.path.join(root, fn)
            if os.path.islink(full):
                continue
            if should_include(full, cfg):
                matches.append(os.path.normpath(full))
    return matches
