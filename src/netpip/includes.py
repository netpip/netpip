"""Find local #include files referenced by an EA source file."""

import re
from pathlib import Path
from typing import Callable, List, Tuple

# Matches: #include "Include\Something.mqh"  (local files only, not <...>)
LOCAL_INCLUDE = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)

MAX_FILES = 50


def collect_sources(
    main_path: Path, read_source: Callable[[Path], str]
) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Read an EA file and the local include files it references.

    Returns (sources, missing). sources is a list of (display name, text).
    missing lists include files that were referenced but not found.
    """
    sources: List[Tuple[str, str]] = []
    missing: List[str] = []
    visited = set()
    queue = [(main_path, main_path.name)]
    while queue and len(visited) < MAX_FILES:
        path, display = queue.pop(0)
        key = path.resolve()
        if key in visited:
            continue
        visited.add(key)
        text = read_source(path)
        sources.append((display, text))
        for name in LOCAL_INCLUDE.findall(text):
            target = path.parent / name.replace("\\", "/")
            if target.is_file():
                queue.append((target, name))
            elif name not in missing:
                missing.append(name)
    return sources, missing
