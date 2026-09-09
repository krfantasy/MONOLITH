"""Headless rebuild script: hermetic tests (no Glyphs, no macOS needed)."""

import runpy
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "rebuild_cli.py"


def _load() -> tuple:
    ns = runpy.run_path(str(SCRIPT))
    return ns["resolve_args"], ns["repo_for"]


def test_save_defaults_to_none() -> None:
    resolve_args, _ = _load()
    assert resolve_args([]).save is None


def test_explicit_save_parsed() -> None:
    resolve_args, _ = _load()
    assert resolve_args(["--save", "/tmp/MONOLITH.glyphs"]).save == Path("/tmp/MONOLITH.glyphs")


def test_repo_from_script_location() -> None:
    _, repo_for = _load()
    assert repo_for("/repo/scripts/rebuild_cli.py", "/elsewhere/doc.glyphs") == Path("/repo")


def test_repo_falls_back_to_doc_dir() -> None:
    _, repo_for = _load()
    assert repo_for(None, "/repo/MONOLITH.glyphs") == Path("/repo")


def test_missing_repo_inputs_exits() -> None:
    import pytest

    _, repo_for = _load()
    with pytest.raises(SystemExit):
        repo_for(None, "")


def test_module_imports_without_glyphs() -> None:
    r = subprocess.run(
        [sys.executable, "-c", "import runpy; runpy.run_path('scripts/rebuild_cli.py')"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r.returncode == 0, r.stderr
