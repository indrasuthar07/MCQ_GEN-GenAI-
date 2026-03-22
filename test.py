"""Lightweight sanity check (no API calls). Run: python test.py"""

import src.mcqgenerator.logger  # noqa: F401
import logging

from src.mcqgenerator.MCQGenerator import _extract_json_object

logging.info("MCQ-Gen test: checking JSON extraction...")
sample = '{"1": {"mcq": "Q?", "options": {"a": "1", "b": "2", "c": "3", "d": "4"}, "correct": "b"}}'
wrapped = f"Here you go:\n```json\n{sample}\n```\n"
assert "correct" in _extract_json_object(wrapped)
print("test.py: OK")
