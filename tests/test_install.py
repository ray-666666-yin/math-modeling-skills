"""Behavior checks run exclusively inside TemporaryDirectory fixtures."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import install
from skill_common import SKILL_NAMES, SafetyError, tree_digest


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="math-skills-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.source = self.base / "checkout" / "skills"
        self.destination = self.base / "user" / "skills"
        self.name = SKILL_NAMES[0]
        self.write_skill(self.name)

    def write_skill(self, name, body="first version"):
        folder = self.source / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: A test-only skill.\n---\n{body}\n", encoding="utf-8"
        )
        (folder / "references").mkdir(exist_ok=True)
        (folder / "references" / "notes.txt").write_text(body, encoding="utf-8")

    def run_install(self, **kwargs):
        return install.install_skills(self.source, self.destination, [self.name], **kwargs)

    def make_link(self, target, link):
        try:
            link.symlink_to(target, target_is_directory=target.is_dir())
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"This runner cannot create symlinks: {error}")

    def test_install_preserves_unrelated_skills_and_repeated_install_is_noop(self):
        unrelated = self.destination / "unrelated"
        unrelated.mkdir(parents=True)
        (unrelated / "keep.txt").write_text("do not touch", encoding="utf-8")
        before = tree_digest(unrelated)
        first = self.run_install()
        self.assertEqual(first["skills"][0]["action"], "install")
        self.assertEqual(tree_digest(self.source / self.name), tree_digest(self.destination / self.name))
        self.assertEqual(tree_digest(unrelated), before)
        destination_before = tree_digest(self.destination)
        repeated = self.run_install()
        self.assertEqual(repeated["skills"][0]["action"], "unchanged")
        self.assertIsNone(repeated["backup"])
        self.assertEqual(tree_digest(self.destination), destination_before)

    def test_update_keeps_complete_old_directory_and_removes_stale_only_by_replacement(self):
        self.run_install()
        target = self.destination / self.name
        (target / "old-only.txt").write_text("user's old local content", encoding="utf-8")
        old = tree_digest(target)
        self.write_skill(self.name, "second version")
        result = self.run_install()
        self.assertEqual(result["skills"][0]["action"], "update")
        backup = Path(result["backup"])
        self.assertEqual(tree_digest(backup / self.name), old)
        self.assertTrue((backup / "restore.json").is_file())
        self.assertFalse((target / "old-only.txt").exists())
        self.assertEqual(tree_digest(target), tree_digest(self.source / self.name))

    def test_dry_run_writes_nothing_for_new_or_existing_destination(self):
        self.run_install(dry_run=True)
        self.assertFalse(self.destination.exists())
        self.run_install()
        before = tree_digest(self.destination)
        self.write_skill(self.name, "new draft")
        self.assertEqual(self.run_install(dry_run=True)["skills"][0]["action"], "update")
        self.assertEqual(tree_digest(self.destination), before)

    def test_selection_does_not_install_other_reviewed_skill(self):
        other = SKILL_NAMES[1]
        self.write_skill(other)
        self.run_install()
        self.assertFalse((self.destination / other).exists())
        with self.assertRaises(SafetyError):
            install.install_skills(self.source, self.destination, ["../outside"])

    def test_rejects_dangerous_or_overlapping_destination(self):
        for destination in (Path(self.base.anchor), Path.home(), self.source, self.source.parent,
                            self.source / self.name, self.source.parent / "another-skills"):
            with self.subTest(destination=destination), self.assertRaises(SafetyError):
                install.install_skills(self.source, destination, [self.name], dry_run=True)

    def test_rejects_existing_target_file_without_changing_it(self):
        self.destination.mkdir(parents=True)
        target = self.destination / self.name
        target.write_text("keep", encoding="utf-8")
        with self.assertRaises(SafetyError):
            self.run_install()
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_rejects_source_symlink(self):
        secret = self.base / "outside.txt"
        secret.write_text("outside fixture", encoding="utf-8")
        self.make_link(secret, self.source / self.name / "escape.txt")
        with self.assertRaises(SafetyError):
            self.run_install()
        self.assertFalse(self.destination.exists())

    def test_rejects_symlink_in_existing_skill(self):
        self.run_install()
        outside = self.base / "outside"
        outside.mkdir()
        self.make_link(outside, self.destination / self.name / "linked")
        with self.assertRaises(SafetyError):
            self.run_install()
        self.assertTrue((self.destination / self.name / "linked").is_symlink())

    def test_rejects_symlink_ancestor_of_destination(self):
        actual = self.base / "actual"
        actual.mkdir()
        alias = self.base / "alias"
        self.make_link(actual, alias)
        with self.assertRaises(SafetyError):
            install.install_skills(self.source, alias / "nested" / "skills", [self.name])
        self.assertEqual(list(actual.iterdir()), [])

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_rejects_windows_junction_without_following_it(self):
        actual = self.base / "junction-target"
        actual.mkdir()
        alias = self.base / "junction-alias"
        # Creation only; all paths belong to this test's temporary directory.
        process = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(actual)],
            capture_output=True,
        )
        if process.returncode:
            self.skipTest("Runner cannot create a directory junction")
        self.addCleanup(lambda: alias.rmdir() if os.path.lexists(alias) else None)
        with self.assertRaises(SafetyError):
            install.install_skills(self.source, alias / "skills", [self.name])
        self.assertEqual(list(actual.iterdir()), [])

    def test_copy_failure_keeps_installed_version(self):
        self.run_install()
        target = self.destination / self.name
        before = tree_digest(target)
        self.write_skill(self.name, "update")
        with patch.object(install.shutil, "copytree", side_effect=OSError("simulated disk failure")):
            with self.assertRaisesRegex(SafetyError, "Staging retained"):
                self.run_install()
        self.assertEqual(tree_digest(target), before)

    def test_promotion_failure_restores_entire_batch(self):
        other = SKILL_NAMES[1]
        self.write_skill(other)
        install.install_skills(self.source, self.destination, [self.name, other])
        old = {name: tree_digest(self.destination / name) for name in (self.name, other)}
        for name in old:
            self.write_skill(name, "update")
        actual_move = install._move

        def interrupted_move(source, target):
            if ".codex-skill-staging" in source.parts and source.name == other:
                raise OSError("simulated promotion failure")
            return actual_move(source, target)

        with patch.object(install, "_move", side_effect=interrupted_move):
            with self.assertRaisesRegex(SafetyError, "rolled back"):
                install.install_skills(self.source, self.destination, [self.name, other])
        for name, fingerprint in old.items():
            self.assertEqual(tree_digest(self.destination / name), fingerprint)

    def test_concurrent_edit_is_preserved_and_aborts_update(self):
        self.run_install()
        self.write_skill(self.name, "update")
        target = self.destination / self.name
        actual_copy = shutil.copytree

        def copy_and_edit(*args, **kwargs):
            result = actual_copy(*args, **kwargs)
            (target / "concurrent.txt").write_text("new user edit", encoding="utf-8")
            return result

        with patch.object(install.shutil, "copytree", side_effect=copy_and_edit):
            with self.assertRaisesRegex(SafetyError, "changed during installation"):
                self.run_install()
        self.assertEqual((target / "concurrent.txt").read_text(encoding="utf-8"), "new user edit")
        self.assertIn("first version", (target / "SKILL.md").read_text(encoding="utf-8"))

    def test_default_destination_honors_codex_home(self):
        with patch.dict(os.environ, {"CODEX_HOME": str(self.base / "custom-home")}):
            self.assertEqual(install.default_destination(), self.base / "custom-home" / "skills")
        with patch.dict(os.environ, {"CODEX_HOME": ""}), patch.object(Path, "home", return_value=self.base / "home"):
            self.assertEqual(install.default_destination(), self.base / "home" / ".codex" / "skills")

    def test_cli_uses_only_isolated_codex_home(self):
        isolated_home = self.base / "cli-codex-home"
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(isolated_home)
        script = Path(install.__file__).resolve()
        command = [sys.executable, str(script), "--skill", self.name]
        dry_run = subprocess.run(command + ["--dry-run"], env=environment, capture_output=True, text=True)
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        self.assertFalse(isolated_home.exists())
        installed = subprocess.run(command, env=environment, capture_output=True, text=True)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertEqual(
            tree_digest(script.parents[1] / "skills" / self.name),
            tree_digest(isolated_home / "skills" / self.name),
        )
        self.assertFalse((isolated_home / "skills" / SKILL_NAMES[1]).exists())


if __name__ == "__main__":
    unittest.main()
