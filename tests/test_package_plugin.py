from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_plugin import package_plugin


class PackagePluginTests(unittest.TestCase):
    def test_package_plugin_includes_runtime_files_and_excludes_repo_only_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            repo_root.mkdir()

            (repo_root / "main.py").write_text("print('main')\n", encoding="utf-8")
            (repo_root / "plugin.json").write_text('{"name": "Decky Secrets"}\n', encoding="utf-8")
            (repo_root / "package.json").write_text('{"name": "decky-secrets"}\n', encoding="utf-8")
            (repo_root / "requirements.txt").write_text("cryptography>=42,<45\n", encoding="utf-8")

            decky_package = repo_root / "decky_secrets"
            decky_package.mkdir()
            (decky_package / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
            (decky_package / "__main__.py").write_text("print('cli')\n", encoding="utf-8")
            (decky_package / "auth.py").write_text("AUTH = True\n", encoding="utf-8")
            (decky_package / "cli.py").write_text("CLI = True\n", encoding="utf-8")
            (decky_package / "clipboard.py").write_text("CLIPBOARD = True\n", encoding="utf-8")
            (decky_package / "vault.py").write_text("VAULT = True\n", encoding="utf-8")

            pycache_dir = decky_package / "__pycache__"
            pycache_dir.mkdir()
            (pycache_dir / "__init__.cpython-313.pyc").write_bytes(b"ignored")

            dist_dir = repo_root / "dist"
            dist_dir.mkdir()
            (dist_dir / "index.js").write_text("console.log('built');\n", encoding="utf-8")
            (dist_dir / "index.js.map").write_text("{}\n", encoding="utf-8")

            (repo_root / "tests").mkdir()
            ((repo_root / "tests") / "test_vault.py").write_text("pass\n", encoding="utf-8")
            (repo_root / "docs").mkdir()
            ((repo_root / "docs") / "spec-wiki-architecture.md").write_text("docs\n", encoding="utf-8")

            package_root, zip_path, manifest_path = package_plugin(repo_root, Path(temp_dir) / "out")

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
