import os

import pytest

from app import create_app, db
from app.models import User, Solver, Game
from config import Config
from datetime import datetime, timezone, timedelta
import sqlalchemy as sa

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'



@pytest.fixture(scope='module')
def new_user():
    user = User(username='a_cool_username', email='aTestEmail@email.com')
    user.set_password('insecurePassword')
    return user


@pytest.fixture(scope='module')
def new_solver(new_user):
    solver = Solver(name='word_guess_solver', user_id=new_user.id)
    return solver


@pytest.fixture(scope='module')
def new_game(new_user, new_solver):
    game = Game(user_id=new_user.id, solver_id=new_solver.id)
    return game


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app(TestConfig)

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client



@pytest.fixture(scope='module')
def init_database(test_client):
    #db.drop_all()
    db.create_all()
    
    # Adding users
    user_1 = User(username='a_user', email='test_email_user1@gmail.com')
    user_1.set_password('testPassword1')
    user_2 = User(username='second_user', email='test_email_user2@gmail.com')
    user_2.set_password('testPassword2')
    user_3  = User(username='test_user_3', email='test_user_3_@gmail.com')
    user_3.set_password('testPassword3')
    db.session.add(user_1)
    db.session.add(user_2)
    db.session.add(user_3)
    db.session.commit()

    # Adding solvers
    solver_1 = Solver(name='solver_1', user_id=1)
    solver_2 = Solver(name='solver_2', user_id=2)
    solver_3 = Solver(name='solver_3', user_id=1, words_played=2, words_won=1)

    db.session.add(solver_1)
    db.session.add(solver_2)
    db.session.add(solver_3)
    db.session.commit()

    # Adding games to test
    game_1 = Game(user_id=1, solver_id=3, correct_word='loser', guesses=6, status=False, results=False)
    game_2 = Game(user_id=1, solver_id=3, correct_word='aisle', guesses=4, current_guess='aisle', current_feedback='GGGGG', status=False, results=True)

    now = datetime.now(timezone.utc) + timedelta(seconds=36000)
    game_3 = Game(user_id=1, solver_id=3, correct_word='tests', status=True, \
                    guesses=2, token='unique_token_1', token_expiration=now)
    game_4 = Game(user_id=2, solver_id=2, correct_word='tests', status=True, \
                    guesses=4, token='unique_token_2', token_expiration=now)

    db.session.add(game_1)
    db.session.add(game_2)
    db.session.add(game_3)
    db.session.add(game_4)
    db.session.commit()

    yield

    # Test Stuff

    db.drop_all()
    


@pytest.fixture(scope='function')
def user_lookup(init_database):
    """Returns user 'a_user' object so don't need to continious look up users when testing class methods in the ORM"""
    user = db.session.scalar(db.select(User).where(User.id == 1))
    return user