"""
Testing the standalone functions inside of the games.py file. 
These functions don't require an active app in order to be run.
"""

import pytest
from app.games import create_payload, update_game


def test_create_payload(new_game):
    """
    GIVEN a new game node,
    WHEN create_payload function is called with new_game,
    THEN check if payload is correct
    """
    test_payload = create_payload(new_game)
    assert isinstance(test_payload, dict)
    assert test_payload["game_token"] == "test_token_abc123"
    assert test_payload["guesses"] == {
        1: {"guess": "tests", "feedback": "BGBBB"}
    }
    assert test_payload["correct_word"] == "hello"
    assert test_payload["message"] == "None"


def test_create_payload_no_feedback(new_game):
    """
    GIVEN a new game node,
    WHEN create_payload function is called with new_game and 
        include_feedback set to False
    THEN check if payload is correct
    """
    test_payload = create_payload(new_game, include_feedback=False)
    assert test_payload["guesses"] == {}


def test_create_payload_no_correct(new_game):
    """
    GIVEN a new game node,
    WHEN create_payload function is called with new_game and 
        include_correct set to False
    THEN check if payload is correct
    """
    test_payload = create_payload(new_game, include_correct=False)
    assert test_payload["correct_word"] == "*****"


def test_create_payload_with_message(new_game):
    """
    GIVEN a new game node,
    WHEN create_payload function is called with new_game and 
        a message
    THEN check if payload is correct
    """
    test_payload = create_payload(new_game, message='Word not found in our dictionary.')
    assert test_payload["message"] == 'Word not found in our dictionary.'


def test_update_game(new_game):
    """
    GIVEN a new game node,
    WHEN update_game is called with a guess and feedback
    THEN check if payload is correct
    """

    update_game(
        game=new_game,
        guess="heath",
        feedback="GGBBB"
    )
    assert new_game.guess_count == 2
    assert new_game.guesses == ["tests", "heath"]
    assert new_game.feedback == ["BGBBB", "GGBBB"]