"""
Development helper functions not used in production. 
Mostly used to fill database between model updates and
to create Games for testing.
"""

from app import db
from .models import Solver, User
from .wordguess import _choose_word, _feedback
from dataclasses import dataclass


# Add Solvers
def add_regex():
    regex = Solver(
        name='regex', 
        user_id=1,
        api_key='987a17e0add886d85f7f465e7cb3fde1'
    )
    db.session.add(regex)
    db.session.commit()
    return



def add_slice():
    slice = Solver(
        name='slice', 
        user_id=1,
        api_key="fe6431e4220cc1e68e08b85d390e94c8"
        )
    db.session.add(slice)
    db.session.commit()


def add_me():
    """
    Script to add a dev user and the test solvers into 
    the database after making changes to the model.
    """
    db.drop_all()
    db.create_all()
    me = User(username='devUser', email='devUser@gmail.com', confirmed=True)
    me.set_password('test_password')
    db.session.add(me)
    db.session.commit()
    add_regex()
    
    
@dataclass
class ExampleGame:
    solver_id: int
    correct_word: str
    guesses: str
    feedback: str
    guess_count: int
    results: bool


def make_game(solver_id: int, results: bool) -> ExampleGame:
    """Helps me create test games for api lookups to fill database."""

    correct_word: str = _choose_word()
    guesses, feedbacks = [], []
    if results == True:
        guess_count = 4
    else:
        guess_count = 6

    for i in range(1, guess_count + 1):
        if results == True and i == guess_count:
            guess = correct_word
            feedback = "GGGGG"
        else:
            while True:
                guess = _choose_word()
                if guess != correct_word:
                    break
            feedback = _feedback(correct_word, guess)
        
        guesses.append(guess)
        feedbacks.append(feedback)
    
    new_game = ExampleGame(
            solver_id = solver_id,
            correct_word = correct_word,
            guesses = ', '.join(guesses),
            feedback = ', '.join(feedbacks),
            guess_count = guess_count,
            results = results
        )

    return new_game


from pathlib import Path
import os

def make_test_games(solver_id: str, won: int = 6, lost: int = 2):
    """
    Writes a .txt file I can copy and paste into the conftest.py file
    """
    this_file = os.path.dirname(__file__)
    new_txt = Path(this_file, 'games.txt')
    with open(new_txt, 'w') as f:
        f.write("games for tests\n\n")
        for i in range(won):
            new_game = make_game(6, True)
            f.write(f"game{i + 1} = Game(\n")
            f.write(f"    solver_id={solver_id},\n")
            f.write(f"    correct_word='{new_game.correct_word}',\n")
            f.write(f"    guess_count={new_game.guess_count},\n")
            f.write(f"    guesses='{new_game.guesses}',\n")
            f.write(f"    feedback='{new_game.feedback}',\n")
            f.write("    status=False,\n")
            f.write("    results=True\n")
            f.write(")\n\n")
            f.write(f"db.session.add(game{i + 1})\n")
        
        f.write("db.session.commit()\n\n")
            
        for j in range(lost):
            new_game = make_game(6, False)
            f.write(f"game{j + 1 + won} = Game(\n")
            f.write(f"    solver_id={solver_id},\n")
            f.write(f"    correct_word='{new_game.correct_word}',\n")
            f.write(f"    guess_count={new_game.guess_count},\n")
            f.write(f"    guesses='{new_game.guesses}',\n")
            f.write(f"    feedback='{new_game.feedback}',\n")
            f.write("    status=False,\n")
            f.write("    results=False\n")
            f.write(")\n\n")
            f.write(f"db.session.add(game{j + 1 + won})\n")

        f.write("db.session.commit()\n")
    return