# wordle clone for python programs
# plays wordle with python wordle solvers


from app import db
from collections import Counter
from .models import Game, Solver
from .words.words import words
from .words.correct import correct_words
import random
import sqlalchemy as sa


def _choose_word():
    length = len(words)
    x = random.randint(0, length - 1)
    return words[x]


def _validate_guess(guess) -> bool:
    if guess in correct_words:
        return True
    return False


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


def create_game(user_id: int, solver_id: int) -> dict:
    new_word = _choose_word()
    new_game = Game(
        user_id = user_id,
        solver_id = solver_id,
        correct_word = new_word
        )
    db.session.add(new_game)
    db.session.commit()
    new_game.get_game_token()
    payload = new_game.to_dict(include_correct=False, include_feedback=False)
    return payload


def game_loop(game_id, guess:str):
    user_game = db.session.scalar(sa.select(Game).where(Game.id == game_id))
    if _validate_guess(guess) == False:
        return user_game.to_dict(
                                include_feedback=False,
                                include_correct=False,
                                message='Word not found in our dictionary.'
                            )
    feedback = _feedback(user_game.correct_word, guess)
    user_game.update_game(guess, feedback)
    if user_game.status == False:
        solver = db.session.scalar(sa.select(Solver).where(Solver.id ==       
                                                        user_game.solver_id))
        solver.update_stats(user_game.results, user_game.guess_count)
        return user_game.to_dict(include_correct=True, include_feedback=True)
    return user_game.to_dict(include_correct=False, include_feedback=True)
    
