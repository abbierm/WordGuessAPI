"""
This file (test_api_lookups.py) tests the view functions api for users to send "GET" requests to view game history data about certain users and solvers.

"""

from flask import current_app


def test_db_connection(init_database):
    """
    GIVEN a flask app configured for testing
    THEN check if the sqlite uri is the correct one for testing
    """
    assert current_app.config["SQLALCHEMY_DATABASE_URI"]  == 'sqlite://'


def test_lookup_solver(test_client, api_lookups, get_lookup_token):
    """
    GIVEN a flask app configured for testing and an api token for user5
    WHEN '/api/lookup_solver/' is requested ("GET") 
    THEN check if the response is valid
    """
    auth = {'Authorization': f"Bearer {get_lookup_token}"}
    response = test_client.get(
        path='api/lookup_solver/solver51',
        headers=auth
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["api_id"] == '123456789qwertyuiopasdfghjklzxcvb'
    assert data["name"] == "solver51"
    assert data["words_played"] == 8
    assert data["words_won"] == 6
    assert data["avg_guesses"] == 4
    assert data["avg_won"] == 75
    assert data["max_streak"] == 6


def test_invalid_api_token_solver_lookup(test_client, api_lookups):
    """
    GIVEN a flask app configured for testing
    WHEN '/api/lookup_solver/solver51' is requested (GET) with an 
        invalid api token
    THEN check if the response is error response is correct
    """
    auth = {"Authorization": "Bearer 038f0663e8d3773d89ec2044f28a5e4b"}
    response = test_client.get(
            path='api/lookup_solver/not_real',
            headers=auth
        )
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Unauthorized"


def test_incorrect_solver_api_lookup(test_client, api_lookups, get_lookup_token):
    """
    GIVEN a configured flask app and a confirmed solver with a valid api token,
    WHEN 'api/lookup_solver/solver41' is requested (GET) (which is a Solver
        that doesn't belong the the user)
    THEN check if the correct error response is returned
    """
    auth = {'Authorization': f"Bearer {get_lookup_token}"}
    response = test_client.get(
        path='api/lookup_solver/solver41',
        headers=auth
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Bad Request"
    assert data["message"] == "Unable to find solver with the name solver41"