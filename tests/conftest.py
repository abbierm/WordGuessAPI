import os

import pytest

from app import create_app, db
from app.models import User, Solver, Game
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'



@pytest.fixture(scope='module')
def new_user():
    user = User(username='a_cool_username')
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
    user_1 = User(username='a_user')
    user_2 = User(username='second_user')
    db.session.add(user_1)
    db.session.add(user_2)
    db.session.commit()

    # Adding solvers
    solver_1 = Solver(name='solver_1', user_id=1)
    solver_2 = Solver(name='solver_2', user_id=2)
    solver_3 = Solver(name='solver_3', user_id=1, words_played=2, words_won=1)

    db.session.add(solver_1)
    db.session.add(solver_2)
    db.session.add(solver_3)
    db.session.commit()

    # Adding Games
    game_1 = Game(user_id=1, solver_id=3, correct_word='loser', guesses=6, status=False, results=False)
    game_2 = Game(user_id=1, solver_id=3, correct_word='aisle', guesses=4, current_guess='aisle', current_feedback='GGGGG', status=False, results=True)
    db.session.add(game_1)
    db.session.add(game_2)
    db.session.commit()

    yield

    # Test Stuff

    db.drop_all()
    print('this happened')


    

