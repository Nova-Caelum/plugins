"""Throwaway driver: install the spawnprobe plugin with one claude binary into a
fresh config dir and ask `claude mcp list` which servers connect.
Usage: python probe/run.py <claude-binary> <label>"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
claude, label = sys.argv[1], sys.argv[2]
claude = shutil.which(claude) or claude
here = Path(__file__).resolve().parent
root = Path(tempfile.mkdtemp(prefix="spawn probe "))
market = root / "market"
shutil.copytree(here / "plugin", market / "plugins" / "spawnprobe")
(market / ".claude-plugin").mkdir(parents=True)
(market / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
    "name": "probe", "owner": {"name": "probe"},
    "plugins": [{"name": "spawnprobe", "source": "./plugins/spawnprobe"}]}), encoding="utf-8")
reports = root / "reports"
env = dict(os.environ, CLAUDE_CONFIG_DIR=str(root / "config dir"), PROBE_OUT=str(reports))
for key in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"):
    env.pop(key, None)
project = root / "my project"
project.mkdir()
NAMES = ("cmdext", "noext", "pyext", "shext", "solo", "projarg", "ctlpython")


def run(args, cwd=None):
    print("$", " ".join(str(a) for a in args), flush=True)
    done = subprocess.run([claude, *args], cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=240)
    print("exit", done.returncode)
    print(done.stdout)
    print(done.stderr, flush=True)
    return done


print("=== label:", label, "claude:", claude, "platform:", sys.platform)
run(["--version"])
run(["plugin", "marketplace", "add", str(market)])
run(["plugin", "install", "spawnprobe@probe", "--scope", "user"])
listing = run(["mcp", "list"], cwd=project)
print("=== reports")
found = {p.stem: p for p in root.rglob("reports/*.json")}
for path in sorted(found.values()):
    print(path)
    print(path.read_text(encoding="utf-8"))
print("=== verdict per server")
for name in NAMES:
    line = next((l for l in listing.stdout.splitlines() if ":" + name + ":" in l or l.strip().startswith("plugin:spawnprobe:" + name)), "")
    ran = name in found
    print("SPAWN %s %-6s %-10s ran=%s line=%s" % (sys.platform, label, name, ran, line.strip()), flush=True)
