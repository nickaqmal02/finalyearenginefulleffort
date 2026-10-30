"""Verify the rootsys key now resolves from .env and is not in source."""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()

from chat_analyzer import langchain_chain as lc  # noqa: E402

print("key loaded:", bool(lc.ROOTSYS_API_KEY), "| len:", len(lc.ROOTSYS_API_KEY))
print("prefix ok:", lc.ROOTSYS_API_KEY.startswith("fiq-"))
print("model:", lc.MODEL_NAME, "| base_url:", lc.ROOTSYS_BASE_URL)
print("redis:", lc.REDIS_URL)
source = open("chat_analyzer/langchain_chain.py").read()
print("literal key still in source:", "fiq-" in source)
