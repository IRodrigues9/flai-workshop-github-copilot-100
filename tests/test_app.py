"""
Tests for the Mergington High School Management System API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participant lists to their original state before each test."""
    original_participants = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        data = response.json()
        activity = data["Basketball Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_known_activity_present(self, client):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data

    def test_chess_club_has_pre_existing_participants(self, client):
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


# ---------------------------------------------------------------------------
# GET /  (redirect)
# ---------------------------------------------------------------------------

class TestRootRedirect:
    def test_root_redirects_to_static(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers["location"]


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alice@mergington.edu"},
        )
        assert response.status_code == 200
        assert "alice@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        client.post(
            "/activities/Soccer Club/signup",
            params={"email": "bob@mergington.edu"},
        )
        response = client.get("/activities")
        participants = response.json()["Soccer Club"]["participants"]
        assert "bob@mergington.edu" in participants

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Underwater Basket Weaving/signup",
            params={"email": "alice@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self, client):
        # michael is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_returns_message(self, client):
        response = client.post(
            "/activities/Drama Club/signup",
            params={"email": "carol@mergington.edu"},
        )
        data = response.json()
        assert "message" in data


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Nonexistent Club/signup",
            params={"email": "alice@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up_returns_404(self, client):
        response = client.delete(
            "/activities/Basketball Team/signup",
            params={"email": "notregistered@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not signed up for this activity"

    def test_unregister_returns_message(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "daniel@mergington.edu"},
        )
        data = response.json()
        assert "message" in data
