from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

PLUGIN_DIR_NAME = "decky-secrets"
INCLUDE_FILES = [
    "main.py",
    "plugin.json",
    "package.json",
    "requirements.txt",
]
INCLUDE_DIRS = [
    "decky_secrets",
    "dist",
]
EXCLUDED_DIRECTORY_NAMES = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc"}


def should_include(path: Path) -> bool:
    return not any(part in EXCLUDED_DIRECTORY_NAMES for part in path.parts) and path.suffix not in EXCLUDED_SUFFIXES


def package_plugin(repo_root: Path, out_dir: Path) -> tuple[Path, Path, Path]:
    package_root = out_dir / PLUGIN_DIR_NAME
    zip_path = out_dir / f"{PLUGIN_DIR_NAME}.zip"
    manifest_path = out_dir / f"{PLUGIN_DIR_NAME}-manifest.json"

    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    included_paths: list[str] = []

    for relative in INCLUDE_FILES:
        source = repo_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"required package file is missing: {relative}")
        destination = package_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        included_paths.append(relative)

    for relative in INCLUDE_DIRS:
        source_dir = repo_root / relative
        if not source_dir.is_dir():
            raise FileNotFoundError(f"required package directory is missing: {relative}")
        destination_dir = package_root / relative
        shutil.copytree(source_dir, destination_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for path in sorted(destination_dir.rglob("*")):
            if path.is_file() and should_include(path.relative_to(package_root)):
                included_paths.append(path.relative_to(package_root).as_posix())

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_root.rglob("*")):
            if path.is_file() and should_include(path.relative_to(package_root)):
                archive.write(path, arcname=path.relative_to(out_dir).as_posix())

    manifest = {
        "plugin_dir": PLUGIN_DIR_NAME,
        "zip_name": zip_path.name,
        "included_files": sorted(included_paths),
        "excluded_examples": [
            "tests/",
            "docs/",
            ".github/",
            "node_modules/",
            ".git/",
            "workspace/framework-only files",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return package_root, zip_path, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the Decky plugin into a Decky Loader friendly zip artifact.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--out-dir", default=Path(__file__).resolve().parents[1] / "build" / "package", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    _, zip_path, manifest_path = package_plugin(repo_root, out_dir)
    print(f"PACKAGED_ZIP={zip_path}")
    print(f"PACKAGE_MANIFEST={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
