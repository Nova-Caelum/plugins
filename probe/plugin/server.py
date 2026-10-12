"""Throwaway stdio MCP server: answers initialize and records how it was started."""
import json
import os
import sys
from pathlib import Path

name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
out = Path(os.environ.get("PROBE_OUT") or Path(__file__).resolve().parent / "reports")
try:
    out.mkdir(parents=True, exist_ok=True)
    (out / (name + ".json")).write_text(json.dumps({
        "name": name, "argv": sys.argv, "executable": sys.executable, "cwd": os.getcwd(),
        "CLAUDE_PROJECT_DIR": os.environ.get("CLAUDE_PROJECT_DIR"),
        "CLAUDE_PLUGIN_ROOT": os.environ.get("CLAUDE_PLUGIN_ROOT"),
        "CLAUDE_PLUGIN_DATA": os.environ.get("CLAUDE_PLUGIN_DATA"),
        "PROBE_OUT_seen": bool(os.environ.get("PROBE_OUT")), "PROBE_VIA": os.environ.get("PROBE_VIA"),
        "HOME": os.environ.get("HOME"), "USERPROFILE": os.environ.get("USERPROFILE"),
    }, indent=1), encoding="utf-8")
except Exception as exc:
    sys.stderr.write("report failed: %r\n" % (exc,))
for line in sys.stdin:
    try:
        msg = json.loads(line)
    except ValueError:
        continue
    if "id" not in msg:
        continue
    method = msg.get("method")
    if method == "initialize":
        result = {"protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "spawnprobe-" + name, "version": "0"}}
    elif method == "tools/list":
        result = {"tools": []}
    else:
        result = {}
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": result}) + "\n")
    sys.stdout.flush()
