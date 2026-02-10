"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have activities
    assert len(data) > 0
    
    # Check structure of first activity
    chess_club = data.get("Chess Club")
    assert chess_club is not None
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    
    # Get initial participant count
    response = client.get("/activities")
    initial_count = len(response.json()[activity_name]["participants"])
    
    # Sign up
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify participant was added
    response = client.get("/activities")
    participants = response.json()[activity_name]["participants"]
    assert email in participants
    assert len(participants) == initial_count + 1


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post(
        "/activities/NonExistentActivity/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Activity not found"


def test_signup_already_registered(client):
    """Test signup when student is already registered"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already registered
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already registered
    
    # Get initial participant count
    response = client.get("/activities")
    initial_count = len(response.json()[activity_name]["participants"])
    
    # Unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify participant was removed
    response = client.get("/activities")
    participants = response.json()[activity_name]["participants"]
    assert email not in participants
    assert len(participants) == initial_count - 1


def test_unregister_activity_not_found(client):
    """Test unregister from non-existent activity"""
    response = client.delete(
        "/activities/NonExistentActivity/unregister",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Activity not found"


def test_unregister_not_registered(client):
    """Test unregister when student is not registered"""
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"].lower()


def test_signup_and_unregister_flow(client):
    """Test complete flow of signing up and then unregistering"""
    activity_name = "Programming Class"
    email = "flowtest@mergington.edu"
    
    # Get initial state
    response = client.get("/activities")
    initial_participants = response.json()[activity_name]["participants"].copy()
    
    # Sign up
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify signup
    response = client.get("/activities")
    participants = response.json()[activity_name]["participants"]
    assert email in participants
    
    # Unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify unregister
    response = client.get("/activities")
    final_participants = response.json()[activity_name]["participants"]
    assert email not in final_participants
    assert final_participants == initial_participants


def test_multiple_students_signup(client):
    """Test multiple students can sign up for the same activity"""
    activity_name = "Drama Club"
    emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
    
    # Get initial count
    response = client.get("/activities")
    initial_count = len(response.json()[activity_name]["participants"])
    
    # Sign up multiple students
    for email in emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify all were added
    response = client.get("/activities")
    participants = response.json()[activity_name]["participants"]
    for email in emails:
        assert email in participants
    assert len(participants) == initial_count + len(emails)
