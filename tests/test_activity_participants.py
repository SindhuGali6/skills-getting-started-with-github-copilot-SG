import uuid

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activity_state():
    original_state = {name: list(details["participants"]) for name, details in activities.items()}
    yield
    for name, details in activities.items():
        details["participants"] = list(original_state[name])


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert set(payload["Chess Club"]) == {"description", "schedule", "max_participants", "participants"}


def test_signup_for_activity_successfully_registers_student():
    activity_name = "Chess Club"
    email = f"signup.success.{uuid.uuid4()}@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_rejects_duplicate_registration():
    activity_name = "Chess Club"
    email = f"signup.duplicate.{uuid.uuid4()}@mergington.edu"

    first_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    second_response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_activity_raises_404_for_missing_activity():
    response = client.post("/activities/Nonexistent Club/signup?email=test@example.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_removes_email_from_activity():
    activity_name = "Chess Club"
    email = f"unregister.{uuid.uuid4()}@mergington.edu"

    signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert signup_response.status_code == 200

    response = client.delete(f"/activities/{activity_name}/participants?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_unregister_participant_missing_email_returns_404():
    activity_name = "Tennis Club"
    email = f"missing.{uuid.uuid4()}@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants?email={email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"
