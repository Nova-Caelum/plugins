"""The install message in README.md must be the message the setup plugin ships.

tests/fixtures/install-message.txt is a byte copy of
plugins/technical-cofounder-setup/reference/install-message.md in the
technical-cofounder repository. When that message changes, refresh the copy:

    git show <ref>:plugins/technical-cofounder-setup/reference/install-message.md \\
        > tests/fixtures/install-message.txt

and this test fails until the README's fenced block is changed to match.
Standard library only.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MESSAGE = ROOT / "tests" / "fixtures" / "install-message.txt"
ADD = "claude plugin marketplace add "
SECTION = "## Already know your way around?"


def fenced_blocks(data):
    """Every fenced block in `data` (bytes), fence lines included, as bytes."""
    blocks, current = [], None
    for line in data.splitlines(keepends=True):
        if current is None:
            if line.startswith(b"```"):
                current = [line]
        else:
            current.append(line)
            if line.rstrip(b"\r\n") == b"```":
                blocks.append(b"".join(current))
                current = None
    return blocks


def the_block(test, path):
    blocks = fenced_blocks(path.read_bytes())
    test.assertEqual(len(blocks), 1, f"{path.name} must hold exactly one fenced block, found {len(blocks)}")
    return blocks[0]


class ReadmeMessageTest(unittest.TestCase):
    def test_readme_block_is_the_message_byte_for_byte(self):
        self.assertEqual(the_block(self, README), the_block(self, MESSAGE))

    def test_already_know_section_adds_the_marketplace_the_way_the_message_does(self):
        in_message = [line.strip() for line in the_block(self, MESSAGE).decode("utf-8").splitlines()
                      if line.strip().startswith(ADD)]
        self.assertEqual(len(in_message), 1, "the message must add the marketplace exactly once")
        section = README.read_text(encoding="utf-8").split(SECTION, 1)[1].split("\n## ", 1)[0]
        in_readme = [line.strip() for line in section.splitlines() if line.strip().startswith(ADD)]
        self.assertEqual(in_readme, in_message)


if __name__ == "__main__":
    unittest.main()
