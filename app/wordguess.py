# wordle clone for python programs
# plays wordle with python wordle solvers


import random
from collections import Counter
import json
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
        'guess_count': 6,
        'username': 'username',
        'status': False,
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

def lookup_game(game_id: int) -> bool:
    try:
        status = GAMES[game_id]['status']
        if status is False:
            return False
        else:
            return True
    except(KeyError):
        print("Game not found")
        print(GAMES)
        return False


def choose_word() -> str:
    length = len(words)
    x = random.randint(0, length - 1)
    return words[x]
    
    
def check_word(user_guess: str):
    if user_guess in correct_words:
        return True
    return False


def make_game(username):
    game_id = max(GAMES.keys()) + 1
    
    correct = choose_word()
    GAMES[game_id] = {
        'correct_word': correct,
        'guess_count': 0,
        'username': username,
        'guesses': {},
        'status': True
    }
    
    return game_id


def give_feedback(correct_word, guess):
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


def update_payload(game_dict: dict, guess: str, feedback: str):
    """game_dict is the 'guesses' nested dictionary in the GAMES dictionary."""
    try:
        guesses = max(game_dict.keys()) + 1
    except(ValueError, KeyError):
        guesses = 1
    game_dict[guesses] = {
                            "guess": guess,
                            "feedback": feedback 
                        }
    return game_dict


def game_to_dict(game_id: int) -> dict:
    final_game_dict = {
        "game_id": game_id,
        "username": GAMES[game_id]["username"],
        "correct_word": GAMES[game_id]["correct_word"],
        "guesses": GAMES[game_id]["guesses"]
    }
    return final_game_dict


def game_loop(game_id, guess):
    if lookup_game(game_id) is False:
        print(GAMES[game_id])
        return {"response": "game-id not found or game is done playing"}
    if not check_word(guess):
        return {"response": f"{guess} not a valid word in our dictionary."}

    GAMES[game_id]['guess_count'] += 1
    feedback = give_feedback(GAMES[game_id]['correct_word'], guess)
    GAMES[game_id]["guesses"] = update_payload(GAMES[game_id]['guesses'], guess, feedback)
    if GAMES[game_id]["guess_count"] == 6:
        GAMES[game_id]["status"] = False
        # Creates a new JSON DOC
        final_game_json = game_to_dict(game_id)
        return final_game_json
    # Only returning "guesses" nested dictionary
    return GAMES[game_id]["guesses"] 
