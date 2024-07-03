"""

This file specifically tests the gameplay api routes start and guess 
inside of the app/api/routes.py file.

"""

def test_start(test_client, init_database):
    """
    GIVEN a configured flask app
    When '/api/start' (POST) is requested with valid 
        solver_api_key and user id
    THEN check if the new game payload returned is correct
    """
    response = test_client.post(
                '/api/start',
                json=dict(
                    solver_api_key="bd64d06a6d271e3a9254afd0e7a94943",
                    user_id=4)
            )

    assert response.status_code == 200
    game_data = response.get_json()
    assert game_data['status'] == True
    assert isinstance(game_data['token'], str) 
    assert game_data['solver_name'] == 'solver43'


def test_guess(test_client, active_game):
    """
    GIVEN a configured flask app
    WHEN '/api/guess' (POST) is requested using a valid 
        game token
    THEN check if the returned payload is correct
    """
    token, game_id = active_game["token"], active_game["game_id"]
    guess_payload = {
            "token": token,
            "game_id": game_id,
            "guess": "fight"
    }

    response = test_client.post(
            path='/api/guess',
            json=guess_payload
        )
    
    assert response.status_code == 200
    game_data = response.get_json()
    assert game_data["guesses"] == {
                "1": {"guess": "fight", "feedback": "BBBBB"}}

    
def test_api_game_loop(test_client, init_database):
    """
    GIVEN a configured flask app 
    WHEN '/api/start' (POST) and 'api/guess' (POST) 
        requests are sent sequentially
    THEN check if responses elicit valid subsequent requests
        Can the app take a starting payload and use the 
        values to make a guess
    """
    # Checking the starting payload
    start_payload = {
            "solver_api_key": "bd64d06a6d271e3a9254afd0e7a94943",
            "user_id": 4
        }
    start_response = test_client.post(
                path='/api/start',
                json=start_payload
            )
    assert start_response.status_code == 200
    token = start_response.get_json()["token"]
    game_id = start_response.get_json()["game_id"]
    
    # Checking the guess payload to previous start
    guess_payload = {
        "token": token,
        "game_id": game_id,
        "guess": "tests"
    }
    guess_response = test_client.post(
            path='api/guess',
            json=guess_payload
        )
    assert guess_response.status_code == 200
    returned_guess_feedback = guess_response.get_json()
    assert returned_guess_feedback["guesses"]["1"]["guess"] == "tests"
    assert returned_guess_feedback["token"] == token


def test_invalid_api_key_non_matching_start(test_client):
    """
    GIVEN a configured flask app 
    WHEN '/api/start' (POST) and is requested with a 
        solver token that does not match the user_id
    THEN check if bad request response matches 
        expected response
    """
    response = test_client.post(
                '/api/start',
                json=dict(
                    solver_api_key="bd64d06a6d271e3a9254afd0e7a94943",
                    user_id=1)
            )
    assert response.status_code == 400
    game_data = response.get_json()
    assert game_data['message'] == "User id doesn't match id from solver_api key.  Check your user id and solve id via our website."


def test_invalid_api_key_start(test_client):
    """
    GIVEN a configured flask app 
    WHEN '/api/start' (POST) and is requested with a 
        solver token that does not exist
    THEN check if bad request response matches 
        expected response
    """
    start_payload = {
            "solver_api_key": "abcdefgijklmnopqabcdefgijklmnopq",
            "user_id": 4
        }

    response = test_client.post(
            '/api/start',
            json=start_payload
            )

    assert response.status_code == 400
    game_data = response.get_json()
    assert game_data["message"] == "User id doesn't match id from solver_api key.  Check your user id and solve id via our website."
    

