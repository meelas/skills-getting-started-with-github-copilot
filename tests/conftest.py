import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture to provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def activities_backup():
    """Fixture to backup original activities data."""
    return deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities(activities_backup):
    """
    Fixture to reset activities to original state before each test.
    This ensures test isolation and data doesn't leak between tests.
    """
    yield
    # Reset after test
    activities.clear()
    activities.update(deepcopy(activities_backup))
