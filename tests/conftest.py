"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import ensure_demo_wav


@pytest.fixture
def demo_wav() -> Path:
    return ensure_demo_wav()
