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


@pytest.fixture()
def new_user():
    user = User(username='a_cool_username', email='aTestEmail@email.com')
    # user.set_password('insecurePassword')
    return user


@pytest.fixture()
def new_solver(new_user):
    solver = Solver(name='word_guess_solver', user_id=1, words_won=0, words_played=0)
    return solver

@pytest.fixture()
def test_client():
    flask_app = create_app(TestConfig)

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client

    

@pytest.fixture()
def init_database(test_client):
    db.create_all()
    
    
    yield

    # Test Stuff

    db.drop_all()
    

@pytest.fixture()
def user_lookup(init_database):
    """
    Returns user 'a_user' object so don't need to continuously look up users when testing class methods in the ORM
    """
    user = User(
            username='a_user_2', 
            email='test_email_user2@gmail.com', 
            confirmed=True)
    user.set_password('test_password')
    db.session.add(user)
    db.session.commit()
    user = db.session.scalar(db.select(User).where(User.username == 'a_user_2'))
    return user


@pytest.fixture()
def solver_lookup(user_lookup, init_database):
    """
    Returns a solver for testing
    """
    solver = Solver(
            name='stats_solver',
            user_id=user_lookup.id,
            words_played=10,
            words_won=8,
            avg_guesses=4.5,
            avg=80,
            max_streak=5,
            current_streak=5,
            api_key='bd64d06a6d271e3a9254afd0e7a94976'
    )
    db.session.add(solver)
    db.session.commit()
    
    return solver



@pytest.fixture()
def preload_solver(init_database):
    user = User(
        username='some_test_user', 
        email='someEmail4Tests@gmail.com', 
        confirmed=True
    )

    db.session.add(user)
    db.session.commit()

    user.set_password('test_password')

    some_user_lookup = db.session.scalar(
            db.select(User).where(
                User.username == 'some_test_user')
        )


    solver = Solver(
        name='someSolver',
        user_id = some_user_lookup.id
    )

    db.session.add(solver)
    db.session.commit()

    solverID = solver.id

    test_game_get_games = Game(
        solver_id=solverID,
        correct_word='tests',
        guess_count=4,
        guesses='aisle, files, texts, tests',
        feedback='BBGBY, BBBYG, GGBGG, GGGGG',
        status=False,
        results=True
    )

    db.session.add(test_game_get_games)
    db.session.commit()

    solver.update_stats(True, 4)

    return solver


@pytest.fixture()
def active_game(init_database, solver_lookup):
    """
    Creates a new user, solver, and an active game. 
    Returns the active game instance
    """

    user = User(
        username='b_user', 
        email='b_user@gmail.com', 
        confirmed=True
    )
    user.set_password('b_test_password')
    db.session.add(user)
    db.session.commit()

    solver = Solver(
        name='someSolver',
        user_id = user.id
    )
    db.session.add(solver)
    db.session.commit()

    active_test_game = Game(
        solver_id=solver.id,
        correct_word='flask'
    )

    db.session.add(active_test_game)
    db.session.commit()

    return active_test_game
