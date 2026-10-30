"""One-shot safety migration: move hardcoded rootsys key into .env (gitignored).

Reads the literal from langchain_chain.py, appends ROOTSYS_API_KEY to .env if absent,
then replaces the assignment with an env lookup. Prints only a masked fingerprint.
"""
from __future__ import annotations

import re
from pathlib import Path

CHAIN = Path("chat_analyzer/langchain_chain.py")
ENV = Path(".env")

src = CHAIN.read_text()
match = re.search(r'^ROOTSYS_API_KEY = "([^"]+)"$', src, re.MULTILINE)
if not match:
    print("SKIP: no literal key assignment found (already migrated?)")
else:
    key = match.group(1)
    env_text = ENV.read_text() if ENV.exists() else ""
    if "ROOTSYS_API_KEY" not in env_text:
        if env_text and not env_text.endswith("\n"):
            env_text += "\n"
        env_text += f"ROOTSYS_API_KEY={key}\n"
        ENV.write_text(env_text)
        print("APPENDED ROOTSYS_API_KEY to .env")
    else:
        print("SKIP: .env already has ROOTSYS_API_KEY")

    masked = key[:4] + "*" * (len(key) - 8) + key[-4:]
    print(f"KEY fingerprint: {masked} (len={len(key)})")
