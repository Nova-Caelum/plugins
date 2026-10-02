#!/usr/bin/env python3
"""Point the three technical-cofounder entries at a new commit.

    python3 scripts/set_tc_sha.py <40-hex sha> [path/to/marketplace.json]

Without a path it edits .claude-plugin/marketplace.json beside this scripts/
folder. Only the `sha` value of each entry whose source is the technical-cofounder
repository changes; every other byte of the file stays as it was. The edit is
checked before it is written: if anything but those three values would differ,
nothing is written. Exit 0 on success (also when the sha is already current),
1 when refused, 2 on usage or an unreadable file. Standard library only.
"""
import copy
import json
import re
import sys
from pathlib import Path

TEAM_URL = "https://github.com/Nova-Caelum/technical-cofounder.git"
SHA = re.compile(r"[0-9a-f]{40}")
SHA_FIELD = re.compile(r'("sha"\s*:\s*")([0-9a-f]{40})(")')
DEFAULT_FILE = Path(__file__).resolve().parent.parent / ".claude-plugin" / "marketplace.json"


def is_team(entry):
    source = entry.get("source") if isinstance(entry, dict) else None
    return isinstance(source, dict) and source.get("url") == TEAM_URL


def rewrite(text, new_sha):
    """`text` with the team entries' shas replaced by new_sha, or ValueError."""
    plugins = json.loads(text)["plugins"]
    team = [entry for entry in plugins if is_team(entry)]
    if len(team) != 3:
        raise ValueError(f"expected three technical-cofounder entries, found {len(team)}")
    old = {entry["source"].get("sha") for entry in team}
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in old):
        raise ValueError("a technical-cofounder entry has no 40-hex sha to replace")

    new_text = SHA_FIELD.sub(lambda m: m.group(1) + new_sha + m.group(3) if m.group(2) in old else m.group(0), text)

    expected = copy.deepcopy(plugins)
    for entry in expected:
        if is_team(entry):
            entry["source"]["sha"] = new_sha
    if json.loads(new_text)["plugins"] != expected:
        raise ValueError("the edit would change something other than the three team shas (another entry shares an old sha?)")
    return new_text


def main(argv):
    if len(argv) not in (2, 3):
        sys.stderr.write("usage: set_tc_sha.py <40-hex sha> [path/to/marketplace.json]\n")
        return 2
    new_sha = argv[1]
    if not SHA.fullmatch(new_sha):
        sys.stderr.write("set_tc_sha: the sha must be 40 lowercase hex characters\n")
        return 1
    path = Path(argv[2]) if len(argv) == 3 else DEFAULT_FILE
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        sys.stderr.write(f"set_tc_sha: cannot read {path}: {error!r}\n")
        return 2
    try:
        new_text = rewrite(text, new_sha)
    except (ValueError, KeyError, TypeError) as error:
        sys.stderr.write(f"set_tc_sha: refused: {error}\n")
        return 1
    if new_text != text:
        path.write_bytes(new_text.encode("utf-8"))
    print(f"technical-cofounder entries pinned to {new_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
