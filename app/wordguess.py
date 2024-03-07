# wordle clone for python programs
# plays wordle with python wordle solvers


import random
from collections import Counter
import json
import secrets
from .words.words import words
from .words.correct import correct_words
from pydantic import BaseModel
from typing import List, Optional
from .models import User, Solver, Game


#====================================================================
##  Game functions outside of a class bc the GAMES 
##  dictionary is going to store all of the game info
#====================================================================


GAMES = {

}

class GuessFeedback(BaseModel):
    guess_number: int
    guess: str
    feedback: Optional[str] = None   


class GameData(BaseModel):
    game_id: str
    username: str
    total_guesses: int
    offical_guesses: int
    correct_word: str
    status: bool = True
    # win/loss
    result: Optional[str] = None
    guesses: Optional[List[GuessFeedback]]


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
        return False


def _validate_status(game_id) -> bool:
    if GAMES[game_id].status is True:
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
    game = GAMES[game_id]
    game.total_guesses += 1
    if valid:
        game.offical_guesses += 1
    game.status = status
    game.result = result
    new_guess = GuessFeedback(
        guess_number = game.total_guesses,
        guess = guess,
        feedback = feedback
    )
    game.guesses.append(new_guess)
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


def create_game(username: str) -> str:
    game_id, correct_word = _create_id(), _choose_word()
    new_game = GameData(
        game_id = game_id,
        username = username,
        total_guesses = 0,
        offical_guesses = 0,
        correct_word = correct_word,
        status = True,
        result = None,
        guesses = []
    )
    GAMES[game_id] = new_game
    return game_id


def create_guess_payload(game_id):
    """Takes out the correct word from the GAMES dict for the GAME. """
    payload = GAMES[game_id].model_dump()
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
    
    # Validates that guess is five characters
    if len(guess) != 5:
        message = f"{guess} is is invalid"
        _update_game(game_id, guess, feedback=None, valid=False)
        return _create_error_response("Guesses must be 5 characters", message)

    # Checks if guess is a valid word
    if not _check_word(guess):
        # Doesn't count as a guess, sends back feedback as None
        _update_game(game_id, guess, feedback=None, valid=False)
        return create_guess_payload(game_id)
        
    feedback = _feedback(GAMES[game_id].correct_word, guess)

    # Check if user won with feedback 'GGGGG'
    if feedback == "GGGGG":
        _update_game(game_id, guess, feedback, status=False, result="won")
        return GAMES[game_id].model_dump()
    
    # Ran out of guesses, after updating the games makes it 6 guesses
    if GAMES[game_id].offical_guesses == 5:
        _update_game(game_id, guess, feedback, status=False, result="lost")
        return GAMES[game_id].model_dump()
        
    # guesses < 5 - Keep playing
    _update_game(game_id, guess, feedback)
    return create_guess_payload(game_id)
    
   



