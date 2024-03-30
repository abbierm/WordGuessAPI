"""
This file (test_views.py) tests the view functions api for users to send "GET" requests to view game history data about certain users and solvers.

"""

from app import create_app, db
from flask import current_app

def test_db_connection(init_database):
    assert current_app.config["SQLALCHEMY_DATABASE_URI"]  == 'sqlite://'


def test_lookup_solver(test_client, init_database):
    """
    Given a flask app configed for testing
    when '/api/lookup_solver/hiro' is requested ("GET")
    Then check if the response is valid
    """
    response = test_client.get('/api/lookup_solver/solver_2')
    assert response.status_code == 200
    x = response.get_json()
    assert x['id'] == 2
    assert x['name'] == 'solver_2'
    assert x['user_id'] == 2
    assert x['words_played'] == 0
    assert x['words_won'] == 0


def test_lookup_solver_with_gamedata(test_client, init_database):
    """
    Given a flask app configed for testing
    WHEN a GET request via the url: '/api/lookup_solver/solver_3' 
    Then check if the response is valid
    """
    response = test_client.get('/api/lookup_solver/solver_3')
    assert response.status_code == 200
    x = response.get_json()
    assert x['id'] == 3
    assert x['name'] == 'solver_3'
    assert x['user_id'] == 1
    assert x['words_played'] == 2
    assert x['words_won'] == 1


def test_lookup_users_solvers(test_client, init_database):
    """
    GIVEN a flask app preconfigured with test data
    WHEN a GET request via the url: '/api/lookup_user_solvers/a_user'
    THEN check if returned json data is consistent with the initialized database
    """
    response = test_client.get('api/lookup_user_solvers/a_user')
    assert response.status_code == 200
    game_data = response.get_json()
    assert game_data["user"]["username"] == 'a_user'
