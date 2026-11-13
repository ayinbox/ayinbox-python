"""Generate src/ayinbox/_async_resources.py from the sync resources.

Usage: python scripts/gen_async.py [--check]
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "ayinbox" / "_resources.py"
DST = ROOT / "src" / "ayinbox" / "_async_resources.py"

CLASSES = [
    "Me",
    "CampaignSteps",
    "CampaignLeads",
    "Campaigns",
    "Contacts",
    "Mailboxes",
    "Unibox",
    "Templates",
    "Webhooks",
    "Analytics",
    "Suppressions",
    "AiTools",
    "AyInbox",
]

HEADER = '"""Async resources. Generated from _resources.py by scripts/gen_async.py: do not edit."""'


def transform(source: str) -> str:
    lines = source.splitlines()
    if not lines[0].startswith('"""'):
        raise SystemExit("unexpected header in _resources.py")
    text = "\n".join([HEADER] + lines[1:]) + "\n"
    text = text.replace("SyncPage", "AsyncPage")
    for name in CLASSES:
        text = re.sub(rf"\b{name}\b", f"Async{name}", text)
    text = text.replace("self._client._request(", "await self._client._request(")
    text = text.replace("self._client._get_page(", "await self._client._get_page(")

    # Make every method whose body awaits into an async def.
    out = text.splitlines()
    i = 0
    while i < len(out):
        match = re.match(r"^(\s*)def ", out[i])
        if match:
            indent = len(match.group(1))
            j = i + 1
            has_await = False
            while j < len(out):
                line = out[j]
                if line.strip() and (len(line) - len(line.lstrip())) <= indent and not line.lstrip().startswith(")"):
                    break
                if "await " in line:
                    has_await = True
                j += 1
            if has_await:
                out[i] = out[i].replace("def ", "async def ", 1)
        i += 1
    return "\n".join(out) + "\n"


def ruff_format(text: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--stdin-filename", str(DST), "-"],
        input=text,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )
    return result.stdout


def main() -> int:
    generated = ruff_format(transform(SRC.read_text()))
    if "--check" in sys.argv:
        current = DST.read_text() if DST.exists() else ""
        if current != generated:
            print("_async_resources.py is out of date: run python scripts/gen_async.py", file=sys.stderr)
            return 1
        return 0
    DST.write_text(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
