import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def rules_only(monkeypatch):
    """Unit tests run without the AI model: fast and deterministic.
    Tests that need it patch classify() or load the model explicitly."""
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MODEL", False)
