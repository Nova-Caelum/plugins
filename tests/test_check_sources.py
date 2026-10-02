"""Tests for scripts/check_sources.py.

Each test writes a marketplace file into a temporary folder and runs the script
the way CI runs it: a separate process, judged by exit code and output.
Standard library only.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_sources.py"

SHA_ONE = "3f43327d2309cfd77419e0197bb3f1ffe0afab08"
SHA_TWO = "ba35bfd90fd31ab99fcf767b20a57db3d4721c11"
TEAM_URL = "https://github.com/Nova-Caelum/technical-cofounder.git"
ENGINE_URL = "https://github.com/Nova-Caelum/hyperspace-engine.git"


def subdir(name, sha=SHA_ONE, url=TEAM_URL):
    return {"name": name, "description": "x",
            "source": {"source": "git-subdir", "url": url, "path": "plugins/" + name, "sha": sha}}


def engine(sha=SHA_TWO, url=ENGINE_URL):
    return {"name": "hyperspace-engine", "description": "x",
            "source": {"source": "url", "url": url, "ref": "hyperspace-engine--v0.1.4", "sha": sha}}


def clean_plugins():
    return [subdir("technical-cofounder"), subdir("technical-cofounder-setup"),
            subdir("super-novacaelum"), engine()]


class CheckSourcesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def check(self, plugins):
        """Run the script on a marketplace holding `plugins`."""
        path = self.tmp / "marketplace.json"
        path.write_text(json.dumps({"name": "m", "owner": {"name": "o"}, "plugins": plugins}), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)

    def assertRefused(self, result, *names):
        self.assertEqual(result.returncode, 1, msg=f"stdout={result.stdout!r} stderr={result.stderr!r}")
        for name in names:
            self.assertIn(name, result.stderr)
        return result.stderr

    def test_clean_marketplace_exits_zero_with_one_line_per_entry(self):
        result = self.check(clean_plugins())
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "technical-cofounder  git-subdir  3f43327d2309",
            "technical-cofounder-setup  git-subdir  3f43327d2309",
            "super-novacaelum  git-subdir  3f43327d2309",
            "hyperspace-engine  url  ba35bfd90fd3",
        ])
        self.assertEqual(result.stderr, "")

    def test_github_source_type_is_refused_even_when_pinned(self):
        bad = {"name": "ssh-trap", "description": "x",
               "source": {"source": "github", "repo": "Nova-Caelum/hyperspace-engine", "sha": SHA_TWO}}
        stderr = self.assertRefused(self.check(clean_plugins() + [bad]), "ssh-trap")
        self.assertIn("github", stderr)

    def test_object_source_without_sha_is_refused(self):
        bad = engine()
        bad["name"] = "unpinned"
        del bad["source"]["sha"]
        self.assertRefused(self.check(clean_plugins() + [bad]), "unpinned")

    def test_a_ref_alone_is_not_a_pin(self):
        bad = engine()
        bad["name"] = "tag-only"
        del bad["source"]["sha"]
        self.assertEqual(bad["source"]["ref"], "hyperspace-engine--v0.1.4")
        self.assertRefused(self.check([bad]), "tag-only")

    def test_sha_must_be_forty_lowercase_hex_characters(self):
        cases = {
            "thirty-nine": SHA_ONE[:-1],
            "forty-one": SHA_ONE + "0",
            "uppercase": SHA_ONE.upper(),
            "not-hex": "g" * 40,
            "short": "3f43327",
            "empty": "",
            "a-tag": "hyperspace-engine--v0.1.4",
            "a-number": 12345,
        }
        for label, sha in cases.items():
            with self.subTest(label):
                bad = subdir("bad-" + label, sha=sha)
                self.assertRefused(self.check([bad]), "bad-" + label)

    def test_non_https_urls_are_refused(self):
        cases = {
            "plain-http": "http://github.com/Nova-Caelum/technical-cofounder.git",
            "ssh-style": "git@github.com:Nova-Caelum/technical-cofounder.git",
            "ssh-scheme": "ssh://git@github.com/Nova-Caelum/technical-cofounder.git",
            "git-scheme": "git://github.com/Nova-Caelum/technical-cofounder.git",
            "local-path": "/tmp/technical-cofounder",
        }
        for label, url in cases.items():
            with self.subTest(label):
                bad = subdir("bad-" + label, url=url)
                stderr = self.assertRefused(self.check([bad]), "bad-" + label)
                self.assertIn("https://", stderr)

    def test_source_with_no_url_is_refused(self):
        bad = subdir("no-url")
        del bad["source"]["url"]
        self.assertRefused(self.check([bad]), "no-url")

    def test_relative_path_string_source_is_refused(self):
        bad = {"name": "local-copy", "description": "x", "source": "./plugins/local-copy"}
        stderr = self.assertRefused(self.check(clean_plugins() + [bad]), "local-copy")
        self.assertIn("relative-path", stderr)

    def test_entry_without_a_source_is_refused_not_a_crash(self):
        bad = {"name": "sourceless", "description": "x"}
        self.assertRefused(self.check(clean_plugins() + [bad]), "sourceless")

    def test_entry_without_a_name_is_refused_by_position_not_a_crash(self):
        bad = engine()
        del bad["name"]  # a fifth entry, otherwise fine: it still cannot be reported without a name
        stderr = self.assertRefused(self.check(clean_plugins() + [bad]), "entry #5")
        self.assertIn("name", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_source_without_a_type_is_refused_not_a_crash(self):
        bad = subdir("typeless")
        del bad["source"]["source"]  # pinned and HTTPS, but no source type to report
        stderr = self.assertRefused(self.check(clean_plugins() + [bad]), "typeless")
        self.assertIn("type", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_every_offending_entry_is_named_and_clean_ones_are_not(self):
        plugins = [
            subdir("fine-one"),
            {"name": "bad-github", "description": "x", "source": {"source": "github", "repo": "a/b", "sha": SHA_ONE}},
            subdir("bad-http", url="http://github.com/Nova-Caelum/technical-cofounder.git"),
            {"name": "bad-relative", "description": "x", "source": "./x"},
            subdir("bad-sha", sha="abc"),
            engine(),
        ]
        result = self.check(plugins)
        stderr = self.assertRefused(result, "bad-github", "bad-http", "bad-relative", "bad-sha")
        self.assertNotIn("fine-one", stderr)
        self.assertNotIn("hyperspace-engine", stderr)
        self.assertEqual(result.stdout, "")

    def test_one_entry_failing_two_rules_has_both_reasons_named(self):
        bad = subdir("double", sha="abc", url="http://github.com/Nova-Caelum/technical-cofounder.git")
        stderr = self.assertRefused(self.check([bad]), "double")
        self.assertIn("sha", stderr)
        self.assertIn("https://", stderr)

    def test_unreadable_marketplace_exits_two(self):
        bad_json = self.tmp / "bad.json"
        bad_json.write_text("{not json", encoding="utf-8")
        no_plugins = self.tmp / "no-plugins.json"
        no_plugins.write_text(json.dumps({"name": "m"}), encoding="utf-8")
        not_a_list = self.tmp / "not-a-list.json"
        not_a_list.write_text(json.dumps({"name": "m", "plugins": {"a": 1}}), encoding="utf-8")
        cases = {"missing": self.tmp / "absent.json", "invalid": bad_json, "no-plugins": no_plugins,
                 "plugins-not-a-list": not_a_list}
        for label, path in cases.items():
            with self.subTest(label):
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, msg=result.stderr)
                self.assertIn(str(path), result.stderr)  # names the file it could not read

    def test_default_file_is_the_one_beside_the_scripts_folder(self):
        root = self.tmp / "repo"
        (root / "scripts").mkdir(parents=True)
        (root / ".claude-plugin").mkdir()
        shutil.copy(SCRIPT, root / "scripts" / "check_sources.py")
        (root / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps({"name": "m", "owner": {"name": "o"}, "plugins": clean_plugins()}), encoding="utf-8")
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        result = subprocess.run([sys.executable, str(root / "scripts" / "check_sources.py")],
                                cwd=elsewhere, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 4)


if __name__ == "__main__":
    unittest.main()
