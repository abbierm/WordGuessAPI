"""

This files specifically tests the gameplay (play.py) routes to start and make a guess to a game. 

"""
import json



def test_start(test_client, init_database):
    """
    Given a flask app and database
    When '/api/start/test_user2/corgi_test_solver'
    Check if newgame payload is correct
    """
    response = test_client.get('/api/start/test_user_3/corgi_test_solver')
    assert response.status_code == 200
    assert 'token' in response.text
    game_data = response.get_json()
    assert game_data['status'] == True
    assert game_data['guesses'] == 0
    assert game_data['solver_name'] == 'corgi_test_solver'


def test_start_invalid_solver_name(test_client, init_database):
    """
    GIVEN a flask app and database
    WHEN 'api/start/new_user3/solver_1' is requested
    CHECK for correct error message
    """
    response = test_client.get('/api/start/test_user_3/solver_1')
    assert response.status_code == 400
    game_data = response.get_json()
    assert game_data['message'] == 'solver name already in user by another user.  Please choose a different name.'


def test_make_guess(test_client, init_database):
    """
    GIVEN a flask app and database with already started wordle games
    WHEN 'api/guess' is requested with POST body of game payload data
    CHECK for correct payload response
    """
    payload = {
        'token': 'unique_token_1',
        'game_id': 3,
        'guess': 'taste'
    }
    response = test_client.post('/api/guess', json=payload)
    game_data = response.get_json()
    print(game_data)
    assert response.status_code == 200

