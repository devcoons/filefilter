# filefilter - File Filter Library

![PyPI - Version](https://img.shields.io/pypi/v/filefilter?style=for-the-badge)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/filefilter?style=for-the-badge)
![PyPI - License](https://img.shields.io/pypi/l/filefilter?style=for-the-badge)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/filefilter?style=for-the-badge&color=%23F0F)
![PyPI - Downloads](https://img.shields.io/pypi/dm/filefilter?style=for-the-badge)

A small, cross-platform Python library for selecting files from a directory tree using **JSON-defined include/exclude filters**.  
It focuses on predictable pattern logic rather than the underlying filesystem walk.

---

##  Features 

- **Pattern-driven filtering** — no manual path checks.
- **Case-insensitive matching** across all platforms.
- **Supports rich glob-style patterns**:
  - `*` → one or more characters  
  - `**` → zero or more characters  
  - Works in both directory and filename segments.
- **Anchored directory semantics**:
  - No prefix → root-anchored
  - `*/` → exactly N levels below root
  - `**/` → anywhere
- **Explicit extension filtering** (`["py", "tar.gz", ".*"]`)
- **Fine-grained include/exclude precedence**
- **Symlinks ignored** (never followed)


### Folder patterns

| Group                             | Example Pattern                 | Meaning (actual behavior)                                                   | Example Matches                                            | Notes / Clever use-cases                            |
| :-------------------------------- | :------------------------------ | :-------------------------------------------------------------------------- | :--------------------------------------------------------- | :-------------------------------------------------- |
| **Root-anchored**                 | `/folder`                       | Match directory named `folder` directly under the root directory            | `/folder`, `/folder/file.txt`                              | Root only                                           |
|                                   | `/folder/*`                     | Match subdirectories **one level** under `/folder`                          | `/folder/a`                                                | Single depth                                        |
|                                   | `/folder/*/*`                   | Match subdirectories **two levels** under `/folder`                         | `/folder/a/b`                                              | Exact depth control                                 |
|                                   | `/folder/**`                    | Match `/folder` and all its subdirectories recursively                      | `/folder/x/y`                                              | Deep traversal                                      |
|                                   | `/folder/**/a`                  | Match any nested `a` under `/folder`                                        | `/folder/a`, `/folder/x/y/a`                               | Anchored root start                                 |
| **Relative (no prefix)**          | `folder`                        | Same as `/folder`, relative to `root_dir`                                   | `/folder`                                                  | Root alias                                          |
|                                   | `folder/*`                      | Match subdirectories one level below `folder`                               | `/folder/sub`                                              | Controlled depth                                    |
|                                   | `folder/*/*`                    | Match directories two levels below `folder`                                 | `/folder/a/b`                                              | Exact two levels                                    |
|                                   | `folder/**`                     | Match `folder` and all subdirectories recursively                           | `/folder/x/y`                                              | Recursive within folder                             |
| **Single-level leading wildcard** | `*/folder`                      | Match any `folder` one level below any top-level dir                        | `/src/folder`, `/data/folder`                              | “Exactly one level up”                              |
|                                   | `*/folder/**`                   | Same as above, but include everything under each matched folder             | `/src/folder/x/y`                                          | Deep from one-level up                              |
| **Multi-level leading wildcard**  | `*/*/folder`                    | `folder` that is **two levels** below any top-level dir                     | `/apps/web/folder`, `/lib/core/folder`                     | “Exactly two levels up”                             |
|                                   | `*/*/*/folder`                  | `folder` that is **three levels** below any top-level dir                   | `/a/b/c/folder`                                            | Scale to N levels: repeat `*/`                      |
|                                   | `*/*/*/*/folder/**`             | Same as above, then **recursive** under `folder`                            | `/a/b/c/d/folder/x/y`                                      | Useful in deep monorepos                            |
| **Recursive leading wildcard**    | `**/folder`                     | Match any directory named `folder` at any depth                             | `/folder`, `/a/b/c/folder`                                 | “Any depth before”                                  |
|                                   | `**/folder/**`                  | Match any directory `folder` and all subdirectories under it                | `/folder/x`, `/x/y/folder/z`                               | Fully recursive                                     |
|                                   | `**`                            | Match **all directories**                                                   | (everything)                                               | Wildcard all                                        |
|                                   | `**/**`                         | Same as `**`                                                                | (everything)                                               | Redundant doublestar                                |
| **Mixed / Middle wildcards**      | `folder/**/sub`                 | Match any `sub` folder nested inside `folder` (any depth gap)               | `/folder/x/y/sub`                                          | “Any depth in between”                              |
|                                   | `*/folder/**/sub`               | Match any `sub` inside any `folder` one level below any root dir            | `/a/folder/sub`, `/a/folder/x/y/sub`                       | Combined leading + middle wildcards                 |
|                                   | `**/folder/another`             | Match any `another` directly inside any `folder` at any depth               | `/folder/another`, `/x/folder/another`                     | Common nested pattern                               |
|                                   | `**/pkg/*`                      | Match **one level after** any `pkg` at any depth                            | `/pkg/a`, `/x/y/pkg/z`                                     | Limit scope to immediate children                   |
|                                   | `**/pkg/*/*`                    | Match **two levels after** any `pkg` at any depth                           | `/pkg/a/b`, `/x/y/pkg/z/t`                                 | Exact depth after target                            |
|                                   | `/modules/*/test`               | A `test` dir exactly one level under `/modules/<name>`                      | `/modules/auth/test`, `/modules/pay/test`                  | Standard per-module test folder                     |
|                                   | `/apps/**/dist`                 | Any `dist` inside `/apps`                                                   | `/apps/web/dist`, `/apps/mobile/a/b/dist`                  | Clean build artifacts                               |
| **Clever use-cases (post-patch)** | `*/*/folder/*/another_folder`   | **Exactly 1** segment between `folder` and `another_folder`                 | `a/b/folder/c/another_folder`                              | Middle `*` now means one segment                    |
|                                   | `*/*/folder/**/another_folder`  | **Any number (0+)** of segments between them                                | `a/b/folder/another_folder`, `a/b/folder/x/another_folder` | Use when the gap can vary                           |
|                                   | `*/*/folder/*/*/another_folder` | **Exactly 2** segments between them                                         | `a/b/folder/x/y/another_folder`                            | Chain `*` for exact middle depth                    |
|                                   | `**/services/**/migrations/*`   | Immediate children under any `migrations` inside any `services` subtree     | `/x/services/a/migrations/001`, `/services/m/2`            | “Find migration versions but not nested subfolders” |
|                                   | `**/features/*/*`               | Exactly **two** levels under any `features` directory                       | `/a/features/x/y`, `/features/p/q`                         | Depth-limited collection                            |
|                                   | `/packages/*/**/dist`           | Any `dist` under any direct child of `/packages`                            | `/packages/core/dist`, `/packages/ui/x/y/dist`             | Works across package families                       |
| **Literal / Edge cases**          | `**/folder/***/anotherfolder`   | Requires a **literal** `***` directory between `folder` and `anotherfolder` | `/folder/***/anotherfolder`                                | `***` is literal (not wildcard)                     |
|                                   | `/folder/***/anotherfolder`     | Same, but anchored at root                                                  | `/folder/***/anotherfolder`                                | Rare in practice                                    |
| **Edge / invalid**                | `/` (or empty)                  | Ignored / invalid after normalization                                       | —                                                          | Stripped by normalization                           |

### File patterns


| Group                             | Example Pattern             | Meaning (actual behavior)                                                                | Example Matches                                                | Notes / Clever use-cases                                                  |
| :-------------------------------- | :-------------------------- | :--------------------------------------------------------------------------------------- | :------------------------------------------------------------- | :------------------------------------------------------------------------ |
| **Root-anchored**                 | `/file.py`                  | Match `file.py` **at project root**                                                      | `/file.py`                                                     | Exact root match                                                          |
|                                   | `/README.*`                 | Files starting with `README.` at root, with **at least one** char after the dot          | `/README.md`, `/README.rst`                                    | Because filename `*` = **1+** chars                                       |
|                                   | `/README.**`                | Files starting with `README.` at root, allowing **zero or more** chars after the dot     | `/README`, `/README.md`, `/README.rst`                         | Filename `**` can match empty                                             |
|                                   | `/.*`                       | Dotfiles at root with **at least one** char after the dot                                | `/.env`, `/.gitignore`                                         | Matches hidden files                                                      |
|                                   | `/folder/*.py`              | Any `.py` directly under `/folder`                                                       | `/folder/a.py`, `/folder/test.py`                              | One level below `/folder`                                                 |
|                                   | `/folder/**/test_*.py`      | `test_*.py` anywhere under `/folder`                                                     | `/folder/test_a.py`, `/folder/x/y/test_utils.py`               | Classic recursive test selector                                           |
| **Relative (no prefix)**          | `Makefile`                  | Match `Makefile` at project root                                                         | `/Makefile`                                                    | Case-insensitive                                                          |
|                                   | `*.toml`                    | Any `.toml` file directly under the root directory                                       | `/pyproject.toml`                                              | Only at root; use `**/*.toml` for recursive                               |
|                                   | `**/*.toml`                 | Any `.toml` file **anywhere**                                                            | `/pyproject.toml`, `/pkg/a/b/config.toml`                      | Recursive                                                                 |
|                                   | `folder/**/*.md`            | Any `.md` anywhere under `folder`                                                        | `/folder/README.md`, `/folder/docs/a/b/guide.md`               | Folder-scoped recursion                                                   |
| **Single-level leading wildcard** | `*/Dockerfile`              | `Dockerfile` exactly **one** directory deep                                              | `/api/Dockerfile`, `/web/Dockerfile`                           | “One level up”                                                            |
|                                   | `*/LICENSE*`                | Files whose name starts with `LICENSE` exactly one level deep                            | `/pkg/LICENSE`, `/lib/LICENSE-MIT`                             | Filename `*` = 1+ chars (so `LICENSE` alone won’t match; use `LICENSE**`) |
| **Multi-level leading wildcard**  | `*/*/Makefile`              | `Makefile` exactly **two** directories deep                                              | `/x/y/Makefile`, `/apps/web/Makefile`                          | Repeat `*/` to require N levels                                           |
|                                   | `*/*/*/package.json`        | `package.json` exactly **three** directories deep                                        | `/a/b/c/package.json`                                          | Deep monorepo layouts                                                     |
| **Recursive leading wildcard**    | `**/Makefile`               | `Makefile` at **any depth**                                                              | `/Makefile`, `/a/Makefile`, `/a/b/c/Makefile`                  | Ignore structure depth                                                    |
|                                   | `**/*.py`                   | Any `.py` file at any depth                                                              | `/a.py`, `/pkg/mod/x.py`, `/x/y/z/__init__.py`                 | Global Python selection                                                   |
|                                   | `**`                        | **All files** (filename `**` matches empty, so any name)                                 | Every file                                                     | Combine with directory excludes to prune                                  |
| **Mixed / middle wildcards**      | `src/**/test_*.py`          | Any `test_*.py` under `src`, at any depth                                                | `/src/test_a.py`, `/src/unit/core/test_utils.py`               | Common test pattern                                                       |
|                                   | `**/migrations/*`           | Any file **one level under** a `migrations` dir at any depth                             | `/app/migrations/001.sql`, `/x/y/migrations/init.py`           | Excludes deeper levels; add `/*/*` for exactly two                        |
|                                   | `**/migrations/*/*`         | Any file **two levels under** a `migrations` dir                                         | `/app/migrations/v1/001.sql`                                   | Exact depth after target                                                  |
|                                   | `**/assets/**/*.png`        | Any `.png` somewhere under any `assets` dir                                              | `/assets/logo.png`, `/x/assets/img/icons/a.png`                | Nested assets                                                             |
|                                   | `/packages/*/**/dist/*.js`  | `.js` directly in any `dist` below any direct child of `/packages`                       | `/packages/core/dist/index.js`, `/packages/ui/x/y/dist/app.js` | Package builds                                                            |
|                                   | `**/pkg/*/*/index.*`        | `index.<ext>` exactly two levels under any `pkg` dir                                     | `/pkg/a/b/index.js`, `/x/y/pkg/z/t/index.html`                 | Depth-limited bundle entry                                                |
| **Clever filename globs**         | `**/file*.py`               | Filenames starting with `file` then **≥1** char, ending `.py`                            | `/fileA.py`, `/x/y/file_utils.py`                              | Does **not** match `/file.py` (use `file**.py` for optional tail)         |
|                                   | `**/file**.py`              | `file` plus **0+** chars, `.py`                                                          | `/file.py`, `/x/fileA.py`, `/x/y/file_utils.py`                | Optional tail                                                             |
|                                   | `**/*test*.py`              | Any file with `test` substring and `.py`                                                 | `/test_main.py`, `/x/y/unittest_tools.py`                      | Broad test sweep                                                          |
|                                   | `**/.env**`                 | `.env` or `.env.<suffix>` anywhere                                                       | `/.env`, `/app/.env.local`, `/x/.envrc`                        | Dotfile families                                                          |
|                                   | `**/*.tar.**`               | `.tar` followed by any (even empty) extension                                            | `/a.tar.gz`, `/b/c.tar.bz2`, `/d/e.tar.`                       | `**` in filename can match empty                                          |
|                                   | `**/*.*`                    | Files with a dot and **at least one** char extension                                     | `/a.txt`, `/b/c.tar.gz`                                        | “Has extension” filter                                                    |
|                                   | `**/*.`                     | Filenames ending with a dot                                                              | `/strange.`                                                    | Rare but supported                                                        |
| **Directory gaps (post-patch)**   | `*/*/folder/*/another.py`   | **Exactly 1** directory between `folder` and `another.py`, and 2 before `folder`         | `/a/b/folder/c/another.py`                                     | Middle `*` = one segment (post-patch)                                     |
|                                   | `*/*/folder/**/another.py`  | **Any number (0+)** directories between `folder` and `another.py`, and 2 before `folder` | `/a/b/folder/another.py`, `/a/b/folder/x/y/another.py`         | Flexible gap                                                              |
|                                   | `*/*/folder/*/*/another.py` | **Exactly 2** directories between `folder` and `another.py`, and 2 before `folder`       | `/a/b/folder/x/y/another.py`                                   | Chain `*` for exact middle depth                                          |
| **Exact names at any depth**      | `**/LICENSE**`              | `LICENSE` with optional suffix at any depth                                              | `/LICENSE`, `/pkg/LICENSE-MIT`                                 | Use `**` to allow empty/extra chars                                       |
|                                   | `**/Dockerfile`             | `Dockerfile` at any depth                                                                | `/Dockerfile`, `/services/api/Dockerfile`                      | Service Dockerfiles                                                       |
|                                   | `**/Makefile`               | `Makefile` at any depth                                                                  | `/Makefile`, `/lib/x/Makefile`                                 | Build roots                                                               |
| **Edge / literal cases**          | `**/folder/***/file.txt`    | Requires a **literal** directory named `***` between `folder` and file                   | `/folder/***/file.txt`                                         | `***` is literal, not a wildcard                                          |
|                                   | `folder/*/file.txt`         | **Exactly 1** dir between `folder` and file (post-patch)                                 | `/folder/a/file.txt`                                           | Before the patch, this would not have matched                             |
|                                   | `folder/**/file.txt`        | Any depth between `folder` and file                                                      | `/folder/file.txt`, `/folder/a/b/file.txt`                     | Versatile                                                                 |
| **Gotchas**                       | `file*.py` (at root)        | Requires at least one char after `file`                                                  | Matches `/fileA.py`; **does not** match `/file.py`             | Use `file**.py` if `file.py` should match                                 |
|                                   | `LICENSE*`                  | Requires at least one char after `LICENSE`                                               | Matches `LICENSE-MIT`; **not** `LICENSE`                       | Use `LICENSE**` to include bare `LICENSE`                                 |
|                                   | `?`                         | Not supported                                                                            | —                                                              | Stick to `*` and `**`                                                     |






##  Decision Order (Inclusion / Exclusion Logic)

When scanning files, the library applies filters in this exact sequence:

1️⃣ **Include-file override**  
   - If the file matches any `include.files` pattern → **included immediately**,  
     even if its extension isn’t in `include.extensions`.

2️⃣ **Hard excludes**  
   - If the file extension matches `exclude.extensions` → excluded.  
   - If the full path matches `exclude.files` → excluded.  
   - If its parent directory matches `exclude.dirs` → excluded.



3️⃣ **Inclusion gating**  
   - If there are *any* include patterns (dirs or files), the file must match  
     one of them to be included.  
     Otherwise, it’s excluded.

4️⃣ **Extension whitelist**  
   - If `include.extensions` is not empty, only matching extensions are included.

5️⃣ **Everything else**  
   - Included by default.

---

##  Configuration Schema

```json
{
  "root_dir": ".",
  "filters": {
    "include": {
      "dirs": [],
      "files": [],
      "extensions": []
    },
    "exclude": {
      "dirs": [],
      "files": [],
      "extensions": []
    }
  }
}
```

| Field | Description |
|-------|--------------|
| `root_dir` | Base directory (absolute or relative). |
| `filters.include.dirs` | Directory inclusion patterns. |
| `filters.include.files` | File inclusion patterns (glob-like). |
| `filters.include.extensions` | Extension whitelist. |
| `filters.exclude.*` | Same structure, but acts as exclusion filters. |

---

##  Pattern Rules Recap

| Symbol | Meaning |
|:-------|:--------|
| `*` | one or more characters (no slashes) |
| `**` | zero or more characters (can cross dirs) |
| Leading `**/` | match anywhere in the tree |
| Leading `*/` | match exactly N levels below root |
| Trailing `/**` | match directory and all descendants |
| `.ext` or `ext` | file extension match (case-insensitive) |
| `.*` in extensions | any non-empty extension |

---

##  Examples (Practical Scenarios)

###  Example 1 — Include all `.py` files anywhere

```json
{
  "root_dir": ".",
  "filters": {
    "include": {
      "dirs": ["**"],
      "files": [],
      "extensions": ["py"]
    },
    "exclude": {
      "dirs": [],
      "files": [],
      "extensions": []
    }
  }
}
```

| File Path | Result | Reason |
|------------|---------|--------|
| `main.py` | ✅ | `.py` extension matches |
| `src/app.py` | ✅ | `.py` extension matches |
| `docs/readme.md` | ❌ | wrong extension |
| `a/b/c/module.py` | ✅ | `.py` file anywhere |

> ✅ All `.py` files anywhere in the project.

---

###  Example 2 — Only Python files in root

```json
{
  "root_dir": ".",
  "filters": {
    "include": {
      "dirs": [],
      "files": ["*.py"],
      "extensions": []
    },
    "exclude": {
      "dirs": [],
      "files": [],
      "extensions": []
    }
  }
}
```

| File Path | Result | Reason |
|------------|---------|--------|
| `main.py` | ✅ | matches `*.py` at root |
| `helper.py` | ✅ | matches `*.py` at root |
| `src/app.py` | ❌ | subdirectory, not root |
| `src/helper.py` | ❌ | subdirectory, not root |

> ✅ Matches `.py` files **only in the project root**, not deeper folders.

---

###  Example 3 — Include only certain substructure

```json
{
  "root_dir": ".",
  "filters": {
    "include": {
      "dirs": [],
      "files": ["*/hi/**/hello.py"],
      "extensions": []
    },
    "exclude": {
      "dirs": [],
      "files": [],
      "extensions": []
    }
  }
}
```

| File Path | Result | Reason |
|------------|---------|--------|
| `a/hi/hello.py` | ✅ | matches `*/hi/**/hello.py` |
| `a/hi/x/hello.py` | ✅ | `hi` one level below root, deeper path allowed |
| `hi/hello.py` | ❌ | missing leading dir before `hi` |
| `a/b/hi/hello.py` | ❌ | `hi` too deep |
| `a/hi/hello.txt` | ❌ | wrong filename |

> ✅ Collects any `hello.py` file under a folder named `hi` that is **exactly one level below root**, with any depth below that.

---

###  Example 4 — Exclude specific pattern while including `.py` files

```json
{
  "root_dir": ".",
  "filters": {
    "include": {
      "dirs": ["**"],
      "files": [],
      "extensions": [".py"]
    },
    "exclude": {
      "dirs": [],
      "files": ["*/hi/**/hello.py"],
      "extensions": []
    }
  }
}
```

| File Path | Result | Reason |
|------------|---------|--------|
| `main.py` | ✅ | `.py`, no exclusion hit |
| `src/lib/module.py` | ✅ | `.py`, no exclusion hit |
| `a/hi/hello.py` | ❌ | excluded by `*/hi/**/hello.py` |
| `src/hi/utils/hello.py` | ❌ | matches exclusion pattern |
| `hi/hello.py` | ✅ | not excluded (no leading dir before `hi`) |

> ✅ Includes all `.py` files except those named `hello.py` inside a `hi` folder that is **one directory below root**.

---

###  Example 5 — Directory pattern focus

```json
{
  "root_dir": ".",
  "filters": {
    "include": {
      "dirs": ["**/myfolder/**"],
      "files": [],
      "extensions": ["py"]
    },
    "exclude": {
      "dirs": ["**/__pycache__/**"],
      "files": [],
      "extensions": []
    }
  }
}
```

| File Path | Result | Reason |
|------------|---------|--------|
| `src/myfolder/x/hello.py` | ✅ | inside `myfolder` |
| `src/myfolder/sub/a.py` | ✅ | inside `myfolder` |
| `src/myfolder/__pycache__/cached.py` | ❌ | excluded dir |
| `src/other/hello.py` | ❌ | outside `myfolder` |

> ✅ Collects `.py` files anywhere under directories named `myfolder`, excluding `__pycache__`.

---

###  Example 6 — Combined complex filters

```json
{
  "root_dir": ".",
  "filters": {
    "include": {
      "dirs": ["src/**", "scripts"],
      "files": ["**/*.sh", "*.py"],
      "extensions": ["py", "sh"]
    },
    "exclude": {
      "dirs": ["**/__pycache__/**", "build"],
      "files": ["*/legacy/**"],
      "extensions": ["log"]
    }
  }
}
```

| File Path | Result | Reason |
|------------|---------|--------|
| `src/main.py` | ✅ | `.py`, included dir |
| `scripts/setup.sh` | ✅ | matched by `**/*.sh` |
| `build/config.py` | ❌ | excluded dir `build` |
| `src/legacy/module.py` | ❌ | excluded by `*/legacy/**` |
| `docs/readme.md` | ❌ | wrong extension |
| `src/utils/tool.log` | ❌ | excluded by extension |

> ✅ Keeps `.py` or `.sh` files under `src` or `scripts`, ignoring logs, builds, and legacy directories.

---

## Summary of Behavior

- Exclusions **always win** first.
- A matching `include.files` **forces inclusion**.
- If any include filters exist, at least one must match.
- Extensions act as a **final whitelist**.
- Matching is **case-insensitive** and normalized.
- `**` can span directory boundaries, not just characters.

---

##  Example Usage

```python
from filefilter import *

cfg_json = """{
    "root_dir": ".",
    "filters": {
        "include": { "dirs": ["**"], "files": [], "extensions": ["py"] },
        "exclude": { "dirs": ["__pycache__"], "files": [], "extensions": [] }
    }
}"""

# Deprecated option
files = filter_paths(cfg_json)

# Option 1: one-liner convenience
matched_files = select(cfg_json)

# Option 2: explicit load + scan
rules = load(cfg_json, base="cwd")
matched_files = scan(rules)

# Print any matched file
for f in matched_files:
    print(f)
```

---

##  License

MIT License © 2025 Ioannis D. (devcoons)
