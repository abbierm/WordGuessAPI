# wordle clone for python programs
# plays wordle with python wordle solvers


from app import db, game_cache
from collections import Counter
from .models import Game, Solver
from .words.words import words
from .words.correct import correct_words
import random
import sqlalchemy as sa
from .games import GameNode, create_payload, update_game
from datetime import datetime, timezone, timedelta



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


def _add_game_to_db(game: GameNode) -> None:
    new_game = Game(
            solver_id=game.solver_id,
            user_id=game.user_id,
            guess_count=game.guess_count,
            guesses=game.guesses,
            feedback=game.feedback,
            results=game.results,
            correct_word=game.correct_word
    )
    db.session.add(new_game)
    solver = db.session.scalar(db.select(Solver).where(
                                            Solver.id == game.solver_id))
    solver.update_stats(game.results, game.guess_count)
    db.session.add(solver)
    db.session.commit()
    
    
def create_game(solver_id: int, solver_name: str, user_id: int) -> dict:
    new_word = _choose_word()
    token = game_cache.make_token()
    new_game = GameNode(
            game_token=token,
            token_expiration=datetime.now(timezone.utc) + 
                timedelta(seconds=36000),
            solver_name=solver_name,
            solver_id=solver_id,
            user_id=user_id,
            correct_word=new_word,
            guess_count=0,
        )
    game_cache.put(new_game)
    payload = create_payload(
            game=new_game,
            include_feedback=False,
            include_correct=False
    )
    return payload


def game_loop(game, guess:str): 
    if _validate_guess(guess) == False:
        return create_payload(
                include_feedback=False,
                include_correct=False,
                message='Word not found in our dictionary.'
        )
    
    feedback = _feedback(game.correct_word, guess)
    update_game(game, guess, feedback)
    
    
    if game.status == False:
        _add_game_to_db(game)
        payload = create_payload(game=game)
        game_cache.remove(game.game_token)
        return payload
    return create_payload(
            game=game,
            include_correct=False, 
            include_feedback=True
    )
