"""
test_main_blueprint_routes.py tests the main blueprint routes to make sure they contain the correct content. 
"""

def test_index(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check if the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'WordGuess' in response.data


def test_documentation(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/documentation' page is requested (GET)
    THEN check if the response is valid
    """
    response = test_client.get('/documentation')
    assert response.status_code == 200
    assert b'<h1 class="title">Documentation</h1>' in response.data


def test_user_homepage(test_client, auth):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/user/a_user_2' page is requested when user is logged in
    THEN check if the response is valid
    """

    auth.login()
    response = test_client.get('/user/user2')
    assert response.status_code == 200
    assert b'Hello, user2!' in response.data
