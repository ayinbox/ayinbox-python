from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(importlib.util.find_spec("ruff") is None, reason="needs ruff")
def test_async_resources_are_generated_from_sync() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gen_async.py"), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
