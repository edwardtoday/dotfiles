"""Exercise snapshot recovery and audit failures in isolated filesystems."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "agents" / "skill_catalog.rb"
AUDIT = ROOT / "bin" / "agents-skills-audit"
RESTORE = ROOT / "bin" / "agents-skills-restore"
SNAPSHOT = ROOT / "bin" / "agents-skills-snapshot"


class SkillCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "SKILL.md").write_text(
            "---\nname: example\ndescription: A fixture skill.\n---\nFixture.\n"
        )
        script = self.source / "scripts" / "check.sh"
        script.parent.mkdir()
        script.write_text("#!/bin/sh\nprintf ok\n")
        script.chmod(0o755)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.record = json.loads(self.ruby(
            "require 'json'; puts JSON.generate(SkillCatalog.snapshot(ARGV[0], ARGV[1]))",
            str(self.source), str(self.root / "snapshots"),
        ).stdout)
        self.record.update({
            "name": "example", "runtime_path": str(self.runtime / "example"),
            "origin": {"kind": "local"}, "dependencies": [],
        })
        self.catalog = self.root / "catalog.json"
        self.config = self.root / "skills.yml"
        self.config.write_text(
            f"runtime_catalog: {self.catalog}\nruntime_root: {self.runtime}\n"
            f"state_root: {self.root / 'state'}\n"
        )
        self.save_catalog()

    def ruby(self, program: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["ruby", "-r", str(LIBRARY), "-e", program, *args],
            capture_output=True, text=True, check=check,
        )

    def save_catalog(self) -> None:
        self.catalog.write_text(json.dumps({
            "runtime_roots": [str(self.runtime)], "skills": [self.record],
        }))

    def restore(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(RESTORE), "--config", str(self.config), "--restore-snapshot", "example"],
            capture_output=True, text=True,
        )

    def audit(self) -> dict:
        result = subprocess.run([str(AUDIT), "--config", str(self.config), "--json"],
                                capture_output=True, text=True)
        return json.loads(result.stdout)

    def test_concurrent_snapshot_updates_merge_and_preserve_other_records(self) -> None:
        self.config.write_text(self.config.read_text() +
                               f"installer_lock: {self.root / 'missing-lock.json'}\n"
                               "personal: {skills: []}\nexternal_links: []\n")
        for name in ["one", "two"]:
            folder = self.runtime / name
            folder.mkdir()
            (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Fixture\n---\n")
        processes = [subprocess.Popen([str(SNAPSHOT), "--config", str(self.config), "--skill", name],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for name in ["one", "two"]]
        for process in processes:
            _, errors = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, errors)
        records = json.loads(self.catalog.read_text())["skills"]
        self.assertEqual({record["name"] for record in records}, {"one", "two", "example"})
        self.assertEqual(next(record for record in records if record["name"] == "example"), self.record)

    def test_round_trip_preserves_content_and_executable_mode(self) -> None:
        result = self.restore()
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.runtime / "example"
        self.assertTrue(target.is_symlink())
        self.assertEqual((target / "SKILL.md").read_bytes(), (self.source / "SKILL.md").read_bytes())
        self.assertEqual((target / "scripts/check.sh").stat().st_mode & 0o777, 0o755)
        self.assertEqual(self.audit()["errors"], [])
        self.assertEqual(self.restore().returncode, 0)

    def test_modified_existing_skill_is_never_overwritten(self) -> None:
        target = self.runtime / "example"
        target.mkdir()
        (target / "SKILL.md").write_text("user edits")
        result = self.restore()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((target / "SKILL.md").read_text(), "user edits")
        self.assertTrue(any("drift" in error for error in self.audit()["errors"]))

    def test_corrupt_archive_is_rejected_before_restore(self) -> None:
        Path(self.record["archive"]).write_bytes(b"corrupt")
        result = self.restore()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.runtime / "example").exists())

    def test_parent_traversal_archive_is_rejected(self) -> None:
        archive = Path(self.record["archive"])
        with tarfile.open(archive, "w:gz") as bundle:
            entry = tarfile.TarInfo("../escape")
            entry.size = 4
            bundle.addfile(entry, io.BytesIO(b"oops"))
        self.record["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.save_catalog()
        result = self.restore()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "state/materialized/escape").exists())

    def test_symlink_archive_is_rejected(self) -> None:
        archive = Path(self.record["archive"])
        with tarfile.open(archive, "w:gz") as bundle:
            entry = tarfile.TarInfo("linked")
            entry.type = tarfile.SYMTYPE
            entry.linkname = str(self.root / "outside")
            bundle.addfile(entry)
        self.record["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.save_catalog()
        self.assertNotEqual(self.restore().returncode, 0)

    def test_missing_dependency_is_reported(self) -> None:
        self.assertEqual(self.restore().returncode, 0)
        self.record["dependencies"] = ["missing"]
        self.save_catalog()
        self.assertTrue(any("missing dependency" in error for error in self.audit()["errors"]))

    def test_bytecode_does_not_change_snapshot_fingerprint(self) -> None:
        cache = self.source / "__pycache__"
        cache.mkdir()
        (cache / "fixture.pyc").write_bytes(b"bytecode")
        digest = self.ruby("puts SkillCatalog.fingerprint(ARGV[0])", str(self.source)).stdout.strip()
        self.assertEqual(digest, self.record["tree_sha256"])

    def test_unregistered_skill_is_not_silently_accepted(self) -> None:
        self.assertEqual(self.restore().returncode, 0)
        other = self.runtime / "unregistered"
        other.mkdir()
        (other / "SKILL.md").write_text("unexpected skill")
        self.assertTrue(any("unregistered" in error for error in self.audit()["errors"]))


if __name__ == "__main__":
    unittest.main()
