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

def test_lookup_solver(test_client, api_lookups):
    """
    GIVEN a flask app configured for testing
    when '/api/lookup_solver/' is requested ("GET")
    Then check if the response is valid
    """
    response = test_client.get('api/lookup_solver/solver51')
    data = response.get_json()
    assert response.status_code == 200
    assert data["user_id"] == 5
    assert data["api_key"] == '123456789qwertyuiopasdfghjklzxcvb'
    assert data["name"] == "solver51"
    assert data["words_played"] == 8
    assert data["words_won"] == 6
    assert data["avg_guesses"] == 4
    assert data["avg_won"] == 75
    assert data["max_streak"] == 6

def test_invalid_solver_lookup(test_client, api_lookups):
    """
    GIVEN a flask app configured for testing
    WHEN '/api/lookup_solver/not_real' is requested (GET)
    THEN check if the response is correct
    """
    response = test_client.get('api/lookup_solver/not_real')
    assert response.status_code == 400
    assert b'Unable to find solver with the name not_real' in response.data

def test_lookup_users_solvers(test_client, api_lookups):
    """
    GIVEN a flask app configured for testing
    WHEN 'api/lookup_user_solvers/user5' is requested (GET)
    THEN check if the response is correct
    """
    response = test_client.get('api/lookup_user_solvers/user5')
    assert response.status_code == 200
    data = response.get_json()
    assert data["solvers"]["solver51"]["name"] == "solver51" 


def test_invalid_user_solver_combo(test_client, api_lookups):
    """
    GIVEN a flask app configured for testing
    WHEN 'api/lookup_user_solver/notReal' is requested
    THEN check if the response is correct
    """
    response = test_client.get('api/lookup_user_solvers/notReal')
    assert response.status_code == 400
    assert b'Unable to find a user with the username: notReal'\
          in response.data


