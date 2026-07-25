"""Гарантируем, что корень engine/ на sys.path (для импорта `scripts.*` в тестах)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
