#!/usr/bin/env python3
"""Refuse any marketplace entry that is not a pinned, HTTPS, remote source.

This marketplace holds no plugin code of its own: every entry points at another
repository, over HTTPS, at one exact commit. Usage:

    python3 scripts/check_sources.py [path/to/marketplace.json]

Without an argument it reads .claude-plugin/marketplace.json beside this
scripts/ folder. Exit 0 and one `name  type  sha[0:12]` line per entry when
every entry passes; exit 1 and one `REFUSED name: reason` line on stderr per
offence otherwise; exit 2 when the file cannot be read. Standard library only.
"""
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}")
DEFAULT_FILE = Path(__file__).resolve().parent.parent / ".claude-plugin" / "marketplace.json"


def problems(entry):
    """Every reason this entry is refused (empty when it is fine). An entry that
    passes has a name, a source type and a sha, so it can always be reported."""
    if not isinstance(entry, dict):
        return ["entry is not an object"]
    found = []
    if not (isinstance(entry.get("name"), str) and entry["name"]):
        found.append("no name")
    source = entry.get("source")
    if isinstance(source, str):
        return found + [f"relative-path source {source!r}; this marketplace holds no plugin code of its own"]
    if not isinstance(source, dict):
        return found + ["no source object"]
    kind = source.get("source")
    if not (isinstance(kind, str) and kind):
        found.append("source type is missing")
    if kind == "github":
        found.append("source type github clones over SSH; use url or git-subdir over HTTPS")
    sha = source.get("sha")
    if not (isinstance(sha, str) and SHA.fullmatch(sha)):
        found.append("sha is missing or is not 40 lowercase hex characters")
    url = source.get("url")
    if kind != "github" and not (isinstance(url, str) and url.startswith("https://")):
        found.append("url is missing or does not start with https://")
    return found


def label(entry, position):
    """The entry's name, or its 1-based position in the plugins list when it has none."""
    name = entry.get("name") if isinstance(entry, dict) else None
    return name if isinstance(name, str) and name else f"entry #{position}"


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        plugins = data.get("plugins") if isinstance(data, dict) else None
        if not isinstance(plugins, list):
            raise ValueError("the file has no plugins list")
    except (OSError, ValueError) as error:
        sys.stderr.write(f"check_sources: cannot read plugins from {path}: {error}\n")
        return 2

    refused = [(label(entry, i), reason) for i, entry in enumerate(plugins, 1) for reason in problems(entry)]
    if refused:
        for name, reason in refused:
            sys.stderr.write(f"REFUSED {name}: {reason}\n")
        return 1
    for entry in plugins:
        source = entry["source"]
        print(f"{entry['name']}  {source['source']}  {source['sha'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
