"""Shared fixtures for app tests — single source of truth.

Fixes: Changed client fixture from scope="session" to scope="function" to avoid
shared TestClient state pollution across tests that mutate global app state
(e.g., POST /agent/switch-problem changes _active_problem_id). Session scope
caused cross-test drift as reported in review.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="function")
def client():
    """Function-scoped TestClient — isolated per test to avoid state leakage."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def pb12_config():
    from app.configs.problem_config import load_problem_config
    return load_problem_config("pb-12-itt")
