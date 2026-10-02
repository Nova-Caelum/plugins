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
    """Every reason this entry is refused (empty when it is fine)."""
    source = entry.get("source") if isinstance(entry, dict) else None
    if isinstance(source, str):
        return [f"relative-path source {source!r}; this marketplace holds no plugin code of its own"]
    if not isinstance(source, dict):
        return ["no source object"]
    found = []
    if source.get("source") == "github":
        found.append("source type github clones over SSH; use url or git-subdir over HTTPS")
    sha = source.get("sha")
    if not (isinstance(sha, str) and SHA.fullmatch(sha)):
        found.append("sha is missing or is not 40 lowercase hex characters")
    url = source.get("url")
    if source.get("source") != "github" and not (isinstance(url, str) and url.startswith("https://")):
        found.append("url is missing or does not start with https://")
    return found


def label(entry, index):
    name = entry.get("name") if isinstance(entry, dict) else None
    return name if isinstance(name, str) and name else f"entry #{index}"


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_FILE
    try:
        plugins = json.loads(path.read_text(encoding="utf-8"))["plugins"]
        if not isinstance(plugins, list):
            raise TypeError("plugins is not a list")
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.stderr.write(f"check_sources: cannot read plugins from {path}: {error!r}\n")
        return 2

    refused = [(label(entry, i), reason) for i, entry in enumerate(plugins) for reason in problems(entry)]
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
