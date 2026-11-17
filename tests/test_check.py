from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check
from skill_common import SKILL_NAMES


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="math-skills-check-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        for name in SKILL_NAMES:
            folder = self.root / "skills" / name
            (folder / "references").mkdir(parents=True)
            (folder / "references" / "details.md").write_text("Details.\n", encoding="utf-8")
            (folder / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: >-\n  A useful test skill.\n---\n"
                "[Details](references/details.md)\n[Public upstream](https://github.com/public-maintainer/project)\n",
                encoding="utf-8",
            )
        self.entry = self.root / "skills" / SKILL_NAMES[0] / "SKILL.md"

    def append(self, text):
        with self.entry.open("a", encoding="utf-8") as stream:
            stream.write(text + "\n")

    def test_valid_collection_and_public_usernames_pass(self):
        self.assertEqual(check.check_repository(self.root), [])

    def test_missing_local_reference_is_an_error(self):
        self.append("[Missing](references/not-present.md)")
        self.assertTrue(any("missing local reference" in error for error in check.check_repository(self.root)))

    def test_reference_outside_standalone_skill_is_an_error(self):
        self.append(f"[Other skill](../{SKILL_NAMES[1]}/SKILL.md)")
        self.assertTrue(any("leaves this standalone skill" in error for error in check.check_repository(self.root)))

    def test_fenced_examples_are_not_treated_as_live_links(self):
        self.append("```markdown\n[Example](references/not-present.md)\n```")
        self.assertEqual(check.check_repository(self.root), [])

    def test_private_path_and_secret_report_location_without_echoing_value(self):
        # Assemble a deliberately fake token so repository-wide scanners do not flag this fixture.
        fake_token = "ghp_" + "A" * 36
        self.append("C:/Users/private-person/Desktop/project\n" + fake_token)
        errors = check.check_repository(self.root)
        self.assertTrue(any("workstation-specific home path" in error for error in errors))
        self.assertTrue(any("possible GitHub token" in error for error in errors))
        self.assertNotIn(fake_token, "\n".join(errors))

    def test_bad_frontmatter_and_missing_skill_fail(self):
        self.entry.write_text("No frontmatter.\n", encoding="utf-8")
        errors = check.check_repository(self.root)
        self.assertTrue(any("frontmatter" in error for error in errors))
        (self.root / "skills" / SKILL_NAMES[1]).rename(self.root / "removed-skill")
        self.assertTrue(any("required skill is missing" in error for error in check.check_repository(self.root)))


if __name__ == "__main__":
    unittest.main()
