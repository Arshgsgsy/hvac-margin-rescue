#!/usr/bin/env python3
"""Compatibility wrapper for the LLM packet exporter."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    target = Path(__file__).with_name("04_export_to_llm.py")
    runpy.run_path(str(target), run_name="__main__")
