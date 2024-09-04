"""

This file specifically tests the gameplay api routes start and guess 
inside of the app/api/routes.py file.

"""
from requests.auth import _basic_auth_str

def test_request_token(test_client, init_database):
    """
    GIVEN a configured flask app
    WHEN 'api/tokens' (POST) is requested with a valid 
        BasicAuth header with username and password, 
    THEN check if token is returned
    """
    auth = {'Authorization': _basic_auth_str('user4', 'test_password')}
    r = test_client.post(
        'api/tokens',
        headers=auth
    )
    json_response = r.get_json()
    try:
        token = json_response["token"]
        assert token is not None
    except KeyError:
        assert False


def test_start(test_client, init_database, get_token):
    """
    GIVEN a configured flask app
    When '/api/start' (POST) is requested with valid 
        auth token and solver_id
    THEN check if the new game payload returned is correct
    """
    header = {"Authorization": f"Bearer {get_token}"}
    response = test_client.post(
                '/api/start',
                headers=header,
                json=dict(solver_id="bd64d06a6d271e3a9254afd0e7a94943")
            )

    assert response.status_code == 200
    game_data = response.get_json()
    assert game_data['status'] == True
    assert isinstance(game_data['game_token'], str) 
    assert game_data['solver_name'] == 'solver43'


def test_guess(test_client, active_game):
    """
    GIVEN a configured flask app
    WHEN '/api/guess' (POST) is requested using a valid 
        game token
    THEN check if the returned payload is correct
    """
    game_token = active_game["game_token"]
    guess_payload = {
            "game_token": game_token,
            "guess": "fight"
    }

    response = test_client.post(
            '/api/guess',
            json=guess_payload
        )
    
    assert response.status_code == 200
    game_data = response.get_json()
    assert game_data["guesses"] == {
                "1": {"guess": "fight", "feedback": "BBBBB"}}

    
def test_api_game_loop(test_client, init_database):
    """
    GIVEN a configured flask app 
    WHEN 'api/tokens', /api/start' (POST) and 'api/guess' (POST) 
        requests are sent sequentially
    THEN check if responses elicit valid responses showing that 
        app can take a valid user and solver and run an entire game from start to finish. 
    """
    # Checking the token request
    auth = {'Authorization': _basic_auth_str('user4', 'test_password')}
    token_response = test_client.post(
        'api/tokens',
        headers=auth
        )
    token_json = token_response.get_json()
    try:
        api_token = token_json["token"]
        assert api_token is not None
    except KeyError:
        assert False

    # Checking the starting payload
    token_header = {"Authorization": f"Bearer {api_token}"}
    start_payload = {"solver_id": "bd64d06a6d271e3a9254afd0e7a94943"}
    start_response = test_client.post(
                path='/api/start',
                headers=token_header,
                json=start_payload
            )
    assert start_response.status_code == 200
    game_token = start_response.get_json()["game_token"]
    
    # Checking the guess payload to previous start
    guess_payload = {
        "game_token": game_token,
        "guess": "tests"
    }
    guess_response = test_client.post(
            path='api/guess',
            json=guess_payload
        )
    assert guess_response.status_code == 200
    returned_guess_feedback = guess_response.get_json()
    assert returned_guess_feedback["guesses"]["1"]["guess"] == "tests"
    assert returned_guess_feedback["game_token"] == game_token


def test_invalid_api_token(test_client):
    """
    GIVEN a configured flask app 
    WHEN '/api/start' (POST) and is requested with an invalid token
    THEN check if correct 'Unauthorized' error is returned
    """
    token_header = {"Authorization": "Bearer 9a1c3132784480a62ad8785cf77a6860"}
    response = test_client.post(
                path='/api/start',
                headers=token_header,
                json=dict(solver_id="bd64d06a6d271e3a9254afd0e7a94943")
            )
    assert response.status_code == 401
    game_data = response.get_json()
    assert game_data['error'] == 'Unauthorized'


def test_invalid_solver_id(test_client, get_token):
    """
    GIVEN a configured flask app loaded with Users and Solvers and
        a valid api_token for user4
    WHEN 'api/start' (POST) is requested with a solver_id that doesn't belong
         to the user
    THEN check if correct error response is returned
    """
    token_header = {"Authorization": f"Bearer {get_token}"}
    start_payload = {"solver_id": "bd64d06a6d271e3a9254afd0e7a94978"}
    response = test_client.post(
        path='api/start',
        headers=token_header,
        json=start_payload
    )
    assert response.status_code == 400
    game_data = response.get_json()
    assert game_data["message"] == "Invalid solver_id"