"""
Tests for the High School Activities API using AAA (Arrange-Act-Assert) pattern.

Arrange: Set up test data and preconditions
Act: Perform the action being tested
Assert: Verify the results match expectations
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """
        Should return a dictionary of all activities with correct structure.
        
        Arrange: Client is ready
        Act: GET /activities
        Assert: Response contains all activities with required fields
        """
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_activity_has_required_fields(self, client):
        """
        Should ensure each activity has all required fields.
        
        Arrange: See structure requirements
        Act: GET /activities
        Assert: Each activity has description, schedule, max_participants, participants
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict), f"{activity_name} should be a dict"
            assert required_fields.issubset(activity_data.keys()), \
                f"{activity_name} missing required fields"
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_participants_are_email_strings(self, client):
        """
        Should ensure participants list contains email addresses as strings.
        
        Arrange: Expect email format in participants
        Act: GET /activities
        Assert: All participants are string-formatted emails
        """
        # Arrange
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant, f"{participant} should be an email"


class TestSignupActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup_adds_participant(self, client, activities_backup):
        """
        Should successfully add a new participant to an activity.
        
        Arrange: Choose activity and email
        Act: POST signup with valid activity and email
        Assert: Participant added, response confirms signup
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_increases_participant_count(self, client):
        """
        Should increase participant count when student signs up.
        
        Arrange: Get initial count of Chess Club participants
        Act: Sign up a new student
        Assert: Participant count increased by 1
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        assert updated_count == initial_count + 1

    def test_signup_duplicate_email_returns_400(self, client):
        """
        Should reject signup if student already registered for activity.
        
        Arrange: Student already in participants list
        Act: Try to sign up same student again
        Assert: 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Should reject signup for activity that doesn't exist.
        
        Arrange: Use non-existent activity name
        Act: POST signup with invalid activity
        Assert: 404 error with "Activity not found"
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_only_adds_to_selected_activity(self, client):
        """
        Should only add participant to the selected activity, not others.
        
        Arrange: Get initial counts for multiple activities
        Act: Sign up for one activity
        Assert: Only that activity's count increased
        """
        # Arrange
        target_activity = "Chess Club"
        other_activity = "Programming Class"
        email = "student@mergington.edu"
        
        initial_response = client.get("/activities")
        initial_counts = {
            target_activity: len(initial_response.json()[target_activity]["participants"]),
            other_activity: len(initial_response.json()[other_activity]["participants"])
        }
        
        # Act
        client.post(f"/activities/{target_activity}/signup", params={"email": email})
        
        # Assert
        updated_response = client.get("/activities")
        updated_counts = {
            target_activity: len(updated_response.json()[target_activity]["participants"]),
            other_activity: len(updated_response.json()[other_activity]["participants"])
        }
        
        assert updated_counts[target_activity] == initial_counts[target_activity] + 1
        assert updated_counts[other_activity] == initial_counts[other_activity]


class TestUnregisterActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_successful_unregister_removes_participant(self, client):
        """
        Should successfully remove a participant from an activity.
        
        Arrange: Student is already registered
        Act: DELETE unregister with valid activity and email
        Assert: Participant removed, response confirms unregister
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_decreases_participant_count(self, client):
        """
        Should decrease participant count when student unregisters.
        
        Arrange: Get initial count of Chess Club participants
        Act: Unregister an existing student
        Assert: Participant count decreased by 1
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
        
        # Assert
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        assert updated_count == initial_count - 1

    def test_unregister_not_signed_up_returns_400(self, client):
        """
        Should reject unregister if student is not signed up for activity.
        
        Arrange: Student not in participants list
        Act: Try to unregister student who didn't sign up
        Assert: 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"  # Not registered
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Should reject unregister for activity that doesn't exist.
        
        Arrange: Use non-existent activity name
        Act: DELETE unregister with invalid activity
        Assert: 404 error with "Activity not found"
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_only_removes_from_selected_activity(self, client):
        """
        Should only remove participant from selected activity, not others.
        
        Arrange: Student is registered for multiple activities
        Act: Unregister from one activity
        Assert: Only that activity's count decreased
        """
        # Arrange
        activity_1 = "Chess Club"
        activity_2 = "Drama Club"
        email = "lucy@mergington.edu"  # Already in Drama Club
        
        # First, sign up for both activities
        client.post(f"/activities/{activity_1}/signup", params={"email": email})
        
        initial_response = client.get("/activities")
        initial_counts = {
            activity_1: len(initial_response.json()[activity_1]["participants"]),
            activity_2: len(initial_response.json()[activity_2]["participants"])
        }
        
        # Act: Unregister from activity_2
        client.delete(f"/activities/{activity_2}/unregister", params={"email": email})
        
        # Assert
        updated_response = client.get("/activities")
        updated_counts = {
            activity_1: len(updated_response.json()[activity_1]["participants"]),
            activity_2: len(updated_response.json()[activity_2]["participants"])
        }
        
        assert updated_counts[activity_1] == initial_counts[activity_1]
        assert updated_counts[activity_2] == initial_counts[activity_2] - 1


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_signup_then_unregister_workflow(self, client):
        """
        Should handle complete signup and unregister workflow correctly.
        
        Arrange: New student, activity ready
        Act: 1) Sign up, 2) Verify added, 3) Unregister, 4) Verify removed
        Assert: Participant correctly added then removed
        """
        # Arrange
        activity_name = "Tennis Club"
        email = "newstudent@mergington.edu"
        
        # Act: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Signup successful
        assert signup_response.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
        
        # Act: Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert: Unregister successful
        assert unregister_response.status_code == 200
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]

    def test_multiple_participants_signup_and_unregister(self, client):
        """
        Should correctly manage multiple participants signing up and unregistering.
        
        Arrange: Multiple students to sign up
        Act: Sign up 3 students, then unregister 2
        Assert: Activities reflect correct participant changes
        """
        # Arrange
        activity_name = "Science Club"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Act: Sign up all
        for email in emails:
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert: All added
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == 4  # 1 original + 3 new
        
        # Act: Unregister 2
        client.delete(f"/activities/{activity_name}/unregister", params={"email": emails[0]})
        client.delete(f"/activities/{activity_name}/unregister", params={"email": emails[1]})
        
        # Assert: Correct ones removed
        activities = client.get("/activities").json()
        assert emails[0] not in activities[activity_name]["participants"]
        assert emails[1] not in activities[activity_name]["participants"]
        assert emails[2] in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == 2  # 1 original + 1 new

    def test_data_isolation_between_tests(self, client):
        """
        Should verify that test data is properly isolated (reset between tests).
        
        Arrange: Check initial state
        Act: This test runs after others that modified data
        Assert: Activities still have original participants
        """
        # Arrange
        activity_name = "Chess Club"
        expected_initial_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        
        # Assert: Should be back to original state from fixture reset
        activities = response.json()
        assert activities[activity_name]["participants"] == expected_initial_participants
