"""
Tests for the Mergington High School API
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app, activities

client = TestClient(app)


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_success(self):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Tennis Club" in data
        assert "Basketball Team" in data
        assert data["Tennis Club"]["description"] == "Learn tennis skills and compete in matches"

    def test_get_activities_has_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Tennis Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity in data.items():
            assert isinstance(activity["participants"], list)


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def setup_method(self):
        """Reset activities before each test"""
        activities.clear()
        activities.update({
            "Test Activity": {
                "description": "A test activity",
                "schedule": "Monday 3:00 PM",
                "max_participants": 5,
                "participants": []
            }
        })

    def test_signup_success(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Test%20Activity/signup?email=student@test.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Student" in data["message"] or "student" in data["message"].lower()
        assert "student@test.edu" in activities["Test Activity"]["participants"]

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@test.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self):
        """Test that duplicate signup is rejected"""
        # First signup
        client.post(
            "/activities/Test%20Activity/signup?email=student@test.edu"
        )
        # Try duplicate
        response = client.post(
            "/activities/Test%20Activity/signup?email=student@test.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_multiple_students(self):
        """Test multiple students can sign up for same activity"""
        client.post(
            "/activities/Test%20Activity/signup?email=student1@test.edu"
        )
        response = client.post(
            "/activities/Test%20Activity/signup?email=student2@test.edu"
        )
        assert response.status_code == 200
        assert len(activities["Test Activity"]["participants"]) == 2
        assert "student1@test.edu" in activities["Test Activity"]["participants"]
        assert "student2@test.edu" in activities["Test Activity"]["participants"]


class TestUnregister:
    """Test the POST /activities/{activity_name}/unregister endpoint"""

    def setup_method(self):
        """Reset activities before each test"""
        activities.clear()
        activities.update({
            "Test Activity": {
                "description": "A test activity",
                "schedule": "Monday 3:00 PM",
                "max_participants": 5,
                "participants": ["student1@test.edu", "student2@test.edu"]
            }
        })

    def test_unregister_success(self):
        """Test successful unregister"""
        response = client.post(
            "/activities/Test%20Activity/unregister?email=student1@test.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"] or "student1@test.edu" in data["message"]
        assert "student1@test.edu" not in activities["Test Activity"]["participants"]
        assert "student2@test.edu" in activities["Test Activity"]["participants"]

    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student1@test.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_student_not_found(self):
        """Test unregister for student not in activity"""
        response = client.post(
            "/activities/Test%20Activity/unregister?email=nonexistent@test.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_multiple_students(self):
        """Test unregistering multiple students"""
        client.post(
            "/activities/Test%20Activity/unregister?email=student1@test.edu"
        )
        response = client.post(
            "/activities/Test%20Activity/unregister?email=student2@test.edu"
        )
        assert response.status_code == 200
        assert len(activities["Test Activity"]["participants"]) == 0


class TestRootEndpoint:
    """Test the GET / endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
