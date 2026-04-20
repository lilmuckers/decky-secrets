from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class DeckyImportLayoutTests(unittest.TestCase):
    def test_main_py_loads_backend_package_when_repo_root_is_not_on_sys_path(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        main_py = repo_root / "main.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "decky.py").write_text(
                "class _Logger:\n"
                "    def info(self, *args, **kwargs):\n"
                "        pass\n"
                "logger = _Logger()\n",
                encoding="utf-8",
            )

            script = textwrap.dedent(
                f"""
                import importlib.util
                import os
                import sys

                repo_root = {str(repo_root)!r}
                main_py = {str(main_py)!r}
                os.chdir({str(temp_path)!r})
                sys.path = [{str(temp_path)!r}] + [entry for entry in sys.path if repo_root not in entry]

                spec = importlib.util.spec_from_file_location('decky_plugin_main', main_py)
                module = importlib.util.module_from_spec(spec)
                assert spec.loader is not None
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                print('IMPORT_OK')
                """
            )

            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("IMPORT_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
