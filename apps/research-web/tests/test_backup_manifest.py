"""Keep the cold-backup manifest aligned with the Compose volume contract."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = json.loads((ROOT / "deploy" / "backup-volumes.json").read_text(encoding="utf-8"))
COMPOSE_TEXT = (ROOT / "deploy" / "compose.yaml").read_text(encoding="utf-8")


def compose_volume_keys():
    """Read this package's simple top-level Compose volume declaration."""
    section = COMPOSE_TEXT.split("\nvolumes:\n", 1)[1]
    return set(re.findall(r"(?m)^  ([a-z][a-z0-9_]*):\s*$", section))


class BackupManifestTests(unittest.TestCase):
    def test_manifest_has_exactly_the_nine_compose_volumes(self):
        declared = MANIFEST["volumes"]
        self.assertEqual(MANIFEST["schema_version"], 1)
        self.assertEqual(len(declared), 9)
        self.assertEqual(len(set(declared)), 9)
        self.assertEqual(set(declared), compose_volume_keys())

    def test_manifest_produces_safe_project_owned_volume_names(self):
        project = MANIFEST["compose_project"]
        self.assertRegex(COMPOSE_TEXT, r"(?m)^name: gen24$")
        self.assertEqual(project, "gen24")
        self.assertRegex(project, r"^[a-z][a-z0-9_]*$")
        for key in MANIFEST["volumes"]:
            self.assertRegex(key, r"^[a-z][a-z0-9_]*$")
            self.assertTrue((project + "_" + key).startswith("gen24_"))
