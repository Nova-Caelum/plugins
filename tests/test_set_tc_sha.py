"""Tests for scripts/set_tc_sha.py: one command moves the three team entries to a new commit.

Each test writes a marketplace file into a temporary folder and runs the script
as a separate process. Standard library only.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "set_tc_sha.py"

OLD = "3f43327d2309cfd77419e0197bb3f1ffe0afab08"
NEW = "0123456789abcdef0123456789abcdef01234567"
ENGINE = "ba35bfd90fd31ab99fcf767b20a57db3d4721c11"
TEAM_URL = "https://github.com/Nova-Caelum/technical-cofounder.git"

LINES = [
    '{',
    '  "name": "nova-caelum",',
    '  "owner": {"name": "Nova Caelum", "url": "https://novacaelum.com"},',
    '  "plugins": [',
    '    {"name": "technical-cofounder", "description": "Team: four agents.",',
    '     "source": {"source": "git-subdir", "url": "' + TEAM_URL + '", "path": "plugins/technical-cofounder", "sha": "@OLD@"}},',
    '    {"name": "technical-cofounder-setup", "description": "Setup.",',
    '     "source": {"source": "git-subdir", "url": "' + TEAM_URL + '", "path": "plugins/technical-cofounder-setup", "sha": "@OLD@"}},',
    '    {"name": "super-novacaelum", "description": "Extras.",',
    '     "source": {"source": "git-subdir", "url": "' + TEAM_URL + '", "path": "plugins/super-novacaelum", "sha": "@OLD@"}},',
    '    {"name": "hyperspace-engine", "description": "Engine.",',
    '     "source": {"source": "url", "url": "https://github.com/Nova-Caelum/hyperspace-engine.git", "ref": "hyperspace-engine--v0.1.4", "sha": "@ENGINE@"}}',
    '  ]',
    '}',
]


def marketplace_text(old=OLD, engine=ENGINE, eol="\n"):
    return eol.join(LINES).replace("@OLD@", old).replace("@ENGINE@", engine) + eol


class SetTcShaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.file = self.tmp / "marketplace.json"

    def write(self, text):
        self.file.write_bytes(text.encode("utf-8"))

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_rewrites_the_three_team_entries_and_changes_nothing_else(self):
        before = marketplace_text()
        self.write(before)
        result = self.run_script(NEW, str(self.file))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        after = self.file.read_bytes().decode("utf-8")
        self.assertEqual(after, before.replace(OLD, NEW))  # byte-identical apart from the sha values
        changed = [(a, b) for a, b in zip(before.splitlines(), after.splitlines()) if a != b]
        self.assertEqual(len(changed), 3)
        self.assertEqual(after.count(NEW), 3)
        self.assertIn(ENGINE, after)  # the engine entry keeps its own pin
        self.assertEqual(json.loads(after)["plugins"][3]["source"]["sha"], ENGINE)

    def test_the_current_sha_changes_no_byte(self):
        before = marketplace_text()
        self.write(before)
        result = self.run_script(OLD, str(self.file))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(self.file.read_bytes().decode("utf-8"), before)

    def test_entries_with_different_old_shas_all_move(self):
        stale = "1" * 40
        before = marketplace_text().replace(OLD, stale, 1)  # first team entry is stale
        self.write(before)
        self.assertEqual(self.run_script(NEW, str(self.file)).returncode, 0)
        after = json.loads(self.file.read_bytes().decode("utf-8"))["plugins"]
        self.assertEqual([p["source"]["sha"] for p in after], [NEW, NEW, NEW, ENGINE])

    def test_line_endings_and_layout_are_kept(self):
        before = marketplace_text(eol="\r\n")
        self.write(before)
        self.assertEqual(self.run_script(NEW, str(self.file)).returncode, 0)
        self.assertEqual(self.file.read_bytes().decode("utf-8"), before.replace(OLD, NEW))

        pretty = json.dumps(json.loads(marketplace_text()), indent=4) + "\n"
        self.write(pretty)
        self.assertEqual(self.run_script(NEW, str(self.file)).returncode, 0)
        self.assertEqual(self.file.read_bytes().decode("utf-8"), pretty.replace(OLD, NEW))

    def test_a_sha_that_is_not_forty_lowercase_hex_is_refused_and_the_file_is_untouched(self):
        before = marketplace_text()
        for label, sha in {"short": "3f43327", "forty-one": NEW + "0", "uppercase": NEW.upper(),
                           "not-hex": "g" * 40, "a-branch": "main", "empty": ""}.items():
            with self.subTest(label):
                self.write(before)
                result = self.run_script(sha, str(self.file))
                self.assertEqual(result.returncode, 1, msg=result.stderr)
                self.assertIn("40 lowercase hex", result.stderr)
                self.assertEqual(self.file.read_bytes().decode("utf-8"), before)

    def test_refuses_unless_exactly_three_team_entries_are_found(self):
        two_team = json.loads(marketplace_text())
        del two_team["plugins"][2]
        four_team = json.loads(marketplace_text())
        four_team["plugins"].append(dict(four_team["plugins"][0], name="one-more"))
        for label, data in {"two": two_team, "four": four_team}.items():
            with self.subTest(label):
                before = json.dumps(data, indent=2) + "\n"
                self.write(before)
                result = self.run_script(NEW, str(self.file))
                self.assertEqual(result.returncode, 1, msg=result.stderr)
                self.assertIn("three", result.stderr)
                self.assertEqual(self.file.read_bytes().decode("utf-8"), before)

    def test_refuses_when_another_entry_shares_the_old_sha(self):
        before = marketplace_text(engine=OLD)  # a text swap would also move the engine's pin
        self.write(before)
        result = self.run_script(NEW, str(self.file))
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        self.assertEqual(self.file.read_bytes().decode("utf-8"), before)

    def test_usage_and_unreadable_file_exit_two(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 2, msg=result.stderr)
        self.assertIn("usage", result.stderr)
        absent = self.tmp / "absent.json"
        result = self.run_script(NEW, str(absent))
        self.assertEqual(result.returncode, 2, msg=result.stderr)
        self.assertIn(str(absent), result.stderr)

    def test_default_file_is_the_one_beside_the_scripts_folder(self):
        root = self.tmp / "repo"
        (root / "scripts").mkdir(parents=True)
        (root / ".claude-plugin").mkdir()
        shutil.copy(SCRIPT, root / "scripts" / "set_tc_sha.py")
        target = root / ".claude-plugin" / "marketplace.json"
        target.write_bytes(marketplace_text().encode("utf-8"))
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        result = subprocess.run([sys.executable, str(root / "scripts" / "set_tc_sha.py"), NEW],
                                cwd=elsewhere, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(target.read_bytes().decode("utf-8"), marketplace_text().replace(OLD, NEW))


if __name__ == "__main__":
    unittest.main()
