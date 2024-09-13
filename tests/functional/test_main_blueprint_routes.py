"""
test_main_blueprint_routes.py tests the main blueprint routes to make sure they contain the correct content. 
"""

import pytest
from app import db
from app.models import Solver


def test_index(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check if the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'WordGuess' in response.data


def test_user_homepage(test_client, auth):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/user/user4' page is requested when user is logged in (GET)
    THEN check if the response is valid
    """
    auth.login()
    response = test_client.get('/user/user4')
    assert response.status_code == 200
    assert b'Hello, user4!' in response.data
    auth.logout()


def test_user_not_logged_in_homepage(test_client):
    """
    GIVEN a flask application configured for testing
    WHEN the '/user/user1' page is requested and there is
        no current user logged in
    THEN check if the response is valid
    """
    response = test_client.get('user/user1', follow_redirects=True)
    assert b'Please log in to view this page!' in response.data


def test_reset_solver_post(test_client, init_database, auth):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/reset_solver' page is requested with solver_id in 
        form data (POST)
    THEN check if the returned page is valid and the solver's
        stats were zeroed out and reset
    """
    auth.login()
    form_data=dict(solver=5)
    response = test_client.post(
        '/reset_solver', 
        data=form_data, 
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'solver42' in response.data
    solver = db.session.get(Solver, 5)
    assert solver.words_played == 0
    auth.logout()


def test_delete_solver_route(test_client, auth, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/delete_solver' page is requested with solver_id in 
        form data (POST)
    THEN check if the correct banner is flashed and the solver
        was deleted
    """
    auth.login()
    form_data=dict(solver=5)
    response = test_client.post(
        '/delete_solver', 
        data=form_data, 
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'solver42 has been deleted!!' in response.data
    solver = db.session.get(Solver, 5)
    assert solver == None
    auth.logout()


def test_solver_page_route(test_client, auth, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/solver/solver43' page is requested with the
        solver's logged in user
    THEN check if the returned page is valid and the solver's
        stats were zeroed out and reset
    """
    auth.login()
    response = test_client.get('/solver/solver43', follow_redirects=True)
    assert response.status_code == 200
    assert b"solver43" in response.data
    assert b"ghost, telex, quite" in response.data
    auth.logout()


def test_solver_page_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/solver/solver43' page is requested (GET)
    THEN check if the user is redirected back to the the main page
        with a flash banner telling the user they must be logged in.
    """
    response = test_client.get('/solver/solver43', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to view this page!' in response.data
  

def test_solver_page_not_users_solver(test_client, auth):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/solver/solver11' page is requested (GET) with a logged
        in user
    THEN check if the user is redirected back to their home page
        with a flash banner telling them the solver isn't registered
        under their WordGuess account.
    """
    auth.login()
    response = test_client.get('/solver/solver11', follow_redirects=True)
    assert response.status_code == 200
    assert b'<h1 class="solver-title-text">solver11\'s<br>Page</h1>' \
            not in response.data
    assert b"solver11 is not registered under your WordGuessAPI account." \
            in response.data


def test_create_api_key(test_client, auth, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/create_api_key' page is requested with solver_id in 
        form data (POST)
    THEN check if the user is redirected back to the solver page and the 
        api key has changed
    """
    auth.login()
    response = test_client.post(
                '/create_solver_id',
                data=dict(solver=6),
                follow_redirects=True
            )

    assert response.status_code == 200
    assert b'<h1 class="solver-info-name">solver43\'s page</h1>' in response.data
    assert b"bd64d06a6d271e3a9254afd0e7a94943" not in response.data
    auth.logout()

            
