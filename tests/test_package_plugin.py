from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_plugin import package_plugin


class PackagePluginTests(unittest.TestCase):
    def test_package_plugin_includes_runtime_files_and_excludes_repo_only_files(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as temp_dir:
            package_root, zip_path, manifest_path = package_plugin(repo_root, Path(temp_dir))

            self.assertTrue((package_root / "main.py").is_file())
            self.assertTrue((package_root / "plugin.json").is_file())
            self.assertTrue((package_root / "package.json").is_file())
            self.assertTrue((package_root / "requirements.txt").is_file())
            self.assertTrue((package_root / "decky_secrets" / "__init__.py").is_file())
            self.assertTrue((package_root / "dist" / "index.js").is_file())
            self.assertFalse((package_root / "tests").exists())
            self.assertFalse((package_root / "docs").exists())
            self.assertFalse((package_root / ".github").exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("main.py", manifest["included_files"])
            self.assertIn("decky_secrets/__init__.py", manifest["included_files"])
            self.assertIn("dist/index.js", manifest["included_files"])
            self.assertNotIn("decky_secrets/__pycache__/__init__.cpython-313.pyc", manifest["included_files"])

            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())

            self.assertIn("decky-secrets/main.py", names)
            self.assertIn("decky-secrets/plugin.json", names)
            self.assertIn("decky-secrets/package.json", names)
            self.assertIn("decky-secrets/requirements.txt", names)
            self.assertIn("decky-secrets/decky_secrets/__init__.py", names)
            self.assertIn("decky-secrets/dist/index.js", names)
            self.assertNotIn("decky-secrets/decky_secrets/__pycache__/__init__.cpython-313.pyc", names)
            self.assertNotIn("decky-secrets/tests/test_vault.py", names)
            self.assertNotIn("decky-secrets/docs/spec-wiki-architecture.md", names)


if __name__ == "__main__":
    unittest.main()
