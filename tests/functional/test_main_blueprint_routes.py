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

