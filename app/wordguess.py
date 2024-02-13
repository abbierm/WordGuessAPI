# wordle clone for python programs
# plays wordle with python wordle solvers


import random
from collections import Counter
import json
import secrets
from .words.words import words
from .words.correct import correct_words


# TODO: Figure out a better way to create ids and possibly passwords

#====================================================================
##  Game functions outside of a class bc the GAMES 
##  dictionary is going to store all of the game info
#====================================================================


GAMES = {
    # GAME_ID
    1: {
        'correct_word': 'word', 
        'guess_count': 4,
        'username': 'username',
        'status': False,
        'result': None,
        'guesses': {
                        1: {
                            'guess': 'aisle',
                            'feedback': "BBBBB"
                            },
                        2: {
                            'guess': 'drown',
                            'feedback': "BYYBB"
                            },
                        3: {
                            'guess': 'rough',
                            'feedback': "YYYBY"
                            },
                        4: {
                            'guess': 'humor',
                            'feedback': 'GGGGG'
                            },
                    }
    }
}



def _create_id():
    while True:
        game_id = secrets.token_urlsafe()
        # Makes sure the game_id isn't already a key for another game 
        try:
            GAMES[game_id]
        except(KeyError):
            return game_id


def _validate_id(game_id) -> bool:
    try:
        GAMES[game_id]
        return True
    except(KeyError):
        return false


def _validate_status(game_id) -> bool:
    if GAMES[game_id]["status"] is True:
        return True
    else:
        return False


def _create_error_response(error, message) -> dict:
    error_response = {
        "error": error,
        "message": message
    }
    return error_response


def _choose_word() -> str:
    length = len(words)
    x = random.randint(0, length - 1)
    return words[x]
    
    
def _check_word(user_guess: str) -> bool:
    if user_guess in correct_words:
        return True
    return False


def _update_game(game_id, guess, feedback, valid=True, status=True, result=None):
    """Generic Updater for the GAMES dictionary."""
    try:
        new_guess = max(GAMES[game_id]["guesses"].keys()) + 1
    except(KeyError, ValueError):
        new_guess = 1
    if valid:
        GAMES[game_id]["guess_count"] += 1
    GAMES[game_id]["status"] = status
    GAMES[game_id]["result"] = result
    GAMES[game_id]["guesses"][new_guess] = {
        "guess": guess,
        "feedback": feedback
    } 
    return


def _feedback(correct_word, guess):
    correct_letter_counts = dict(Counter(correct_word))
    feedback_list = [1, 2, 3, 4, 5]
    yellow_letters = []
    for index, letter in enumerate(guess):
        if correct_word[index] == letter:
            feedback_list[index] = "G"
            correct_letter_counts[letter] -= 1
        elif letter not in correct_word:
            feedback_list[index] = "B"
        else:
            yellow_letters.append((index, letter))
    for tup in yellow_letters:
        i, l = tup[0], tup[1]
        if correct_letter_counts[l] > 0:
            feedback_list[i] = "Y"
            correct_letter_counts[l] -= 1
        else:
            feedback_list[i] = "B" 
    return ''.join(feedback_list)


def create_game(username: str) -> dict:
    game_id, correct_word = _create_id(), _choose_word()
    GAMES[game_id] = {
                        "correct_word": correct_word,
                        "username": username,
                        "guess_count": 0,
                        "status": True,
                        "result": None,
                        "guesses": {}
                        }
    return game_id


def create_guess_payload(game_id):
    """Takes out the correct word from the GAMES dict for the GAME. """
    payload = dict(GAMES[game_id])
    payload.pop("correct_word")
    return payload


def game_loop(game_id, guess):
    # Validate game_id (token)
    if not _validate_id(game_id):
        message = f"Your game_id {game_id} is invalid"
        return _create_error_response("game not found", message)

    # Validates that game is still playable via status
    if not _validate_status(game_id):
        message = f"The game for the game_id: {game_id} has already finished and is no longer playable."
        return _create_error_response("game status already complete", message)
    
    # Checks if guess is a valid word
    if not _check_word(guess):
        # Doesn't count as a guess, sends back feedback as None
        _update_game(game_id, guess, feedback=None, valid=False)
        return create_guess_payload(game_id)
        
    feedback = _feedback(GAMES[game_id]["correct_word"], guess)

    # Check if user won with feedback 'GGGGG'
    if feedback == "GGGGG":
        _update_game(game_id, guess, feedback, status=False, result="won")
        return GAMES[game_id]
    
    # Ran out of guesses, after updating the games makes it 6 guesses
    if GAMES[game_id]["guess_count"] == 5:
        _update_game(game_id, guess, feedback, status=False, result="lost")
        return GAMES[game_id]
        
    # guesses < 5 - Keep playing
    _update_game(game_id, guess, feedback)
    return create_guess_payload(game_id)
    
   



