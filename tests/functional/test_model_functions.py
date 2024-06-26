"""
Tests the database function's inside of the application scope.
These tests are different from the unit tests because they require an active database connection in order to work. 

All tests from app.models.py file
"""
import pytest
from app import db
from app.models import User, Game, Solver
from sqlalchemy import exc, func, and_
import sqlalchemy as sa


#====================================================================
# User Model Tests
#====================================================================
def test_adding_user(new_user, init_database):
    """
    GIVEN a configured flask app and initialized database
    WHEN adding and committing a new user to the database
    THEN check that there are no SQLAlchemy Errors
    """
    def add_user():
        try:
            db.session.add(new_user)
            db.session.commit()
            return True
        except exc.SQLAlchemyError:
            return False
    x = add_user()
    assert x == True


def test_new_user_lookup(init_database):
    """
    GIVEN a configured flask app and initialized database
    WHEN adding and committing a new user to the database
    THEN check we can lookup user inside of database
    """
    test_user = User(username='a_new_test', email='helloWORLD@gmail.com')
    test_user.set_password('hashed_password')
    db.session.add(test_user)
    db.session.commit()
    user_lookup = db.session.scalar(sa.select(User).where(
        User.username == 'a_new_test'))
    assert user_lookup.username == 'a_new_test'
    assert user_lookup.email == 'helloWORLD@gmail.com'
    

def test_adding_duplicate_usernames(init_database, user_lookup):
    """
    GIVEN a configured flask app and initialized database
    WHEN calling check_duplicate_username() with 'a_user'
    THEN check if returns True
    """

    assert User.check_duplicate_username('a_user_2') == True


def test_duplicate_email_check(init_database, user_lookup):
    """
    GIVEN a configured flask app and initialized db with registered users
    WHEN calling check_duplicate_email() with 'aTestEmail@email.com'
    THEN check if function returns True
    """

    assert User.check_duplicate_email('test_email_user2@gmail.com') == True


def test_user_to_dict(init_database, user_lookup, solver_lookup):
    """
    GIVEN a configured flask app and database
    WHEN calling to_dict() method for initialized user with username 'a_user'
    THEN check if returned payload is correct
    """
    payload = user_lookup.to_dict()
    assert payload['id'] == 1
    assert payload['username'] == 'a_user_2'
    assert payload['email'] == 'test_email_user2@gmail.com'
    assert payload['solvers'] == ['stats_solver']


def test_check_user_password(init_database, user_lookup):
    """
    GIVEN a configured flask app with testing database
    WHEN calling the User.check_password() function
    THEN check if it returns 'True' for the correct password
    and 'False' for the incorrect password. 
    """
    assert user_lookup.check_password('test_password') == True
    assert user_lookup.check_password('not_a_test_password') == False


def test_generate_confirmation_token(init_database, user_lookup):
    """
    GIVEN a configured flask app with a testing database and a user object
    WHEN calling the User.generate_confirmation_token 
    THEN check if the verify_account returns 'True' for correct
        user
    """
    token = user_lookup.generate_confirmation_token()
    user = User.verify_account(token)
    assert user_lookup.id == user.id


def test_reset_password_token(init_database, user_lookup):
    """
    GIVEN a configured flask app with a testing db and a user instance
    WHEN calling the get_reset_password_token
    THEN checking if the verify_reset_password_token() function works
    """
    reset_token = user_lookup.get_reset_password_token()
    returned_user = User.verify_reset_password_token(reset_token)
    assert user_lookup.id == returned_user.id


#====================================================================
# Solver Model Tests
#==================================================================== 
def test_adding_new_solver(init_database, user_lookup):
    """
    GIVEN a configured flask app, an initialized db, and a user instance
    WHEN adding a new solver
    THEN check if the solver is added and committed to the 
        database by doing a solver query lookup.
    """
    user_id = user_lookup.id
    new_solver = Solver(user_id=user_id, name='corgi_solver')
    db.session.add(new_solver)
    db.session.commit()
    solver = db.session.scalar(db.select(Solver).where(Solver.name == 'corgi_solver'))
    assert solver.user_id == user_lookup.id


def test_solver_to_dict(init_database, solver_lookup):
    """
    GIVEN a configured flask app, database, and a solver instance
    WHEN calling the to_dict() method
    THEN check if if the information is correct.
    """
    payload = solver_lookup.to_dict()
    assert payload["id"] == 1
    assert payload["name"] == 'stats_solver'
    assert payload["user_id"] == 1
    assert payload["words_played"] == 10
    assert payload["words_won"] == 8
    assert payload["avg_won"] == 80
    assert payload["avg_guesses"] == 4.5
    assert payload["max_streak"] == 5
    assert payload["api_key"] =='bd64d06a6d271e3a9254afd0e7a94976'


def test_make_solver_api_key(init_database, solver_lookup):
    """
    GIVEN a configured flask app, database, and a solver instance
    WHEN calling the make_api() method on the solver
    THEN check if API key was created in the correct format
    """
    solver_lookup.make_api_key()
    assert solver_lookup.api_key != 'bd64d06a6d271e3a9254afd0e7a94976'
    assert type(solver_lookup.api_key) == str
    assert len(solver_lookup.api_key) == 32


def test_check_api_key(init_database, solver_lookup):
    """
    GIVEN a configured flask app, database, and a solver instance
    WHEN calling the check_api() static method
    THEN check if the solver returned from check_key is the same as the
        solver_lookup_api
    """
    solver = Solver.check_key('bd64d06a6d271e3a9254afd0e7a94976')
    assert solver.id == solver_lookup.id


def test_check_api_key_incorrect(init_database, solver_lookup):
    """
    GIVEN a configured flask app, database
    WHEN calling the Solver.check_api() static method 
        using a incorrect key
    THEN check if the solver returned from check_key 
        is None
    """
    solver = Solver.check_key('bd64d06a6d271e3a9254afd0e7a94975')
    assert solver is None


def test_get_solver(init_database, solver_lookup):
    """
    GIVEN a configured flask app, database, and solver, 
    WHEN calling the Solver.get_solver() static method
         with the api key, 
    THEN check if the correct solver is returned
    """
    solver = Solver.get_solver('bd64d06a6d271e3a9254afd0e7a94976')
    assert solver_lookup.id == solver.id


def test_validate_user_solver_true(init_database, solver_lookup):
    """
    GIVEN a configured flask app and database
    WHEN calling the static method Solver.validate_user_solver() 
        with a test username and solver name associated with
        that user
    THEN check if the the returned value is True
    """
    assert Solver.validate_user_solver(
        username='a_user_2', solver_name='stats_solver') == True


def test_validate_user_solver_false(init_database, user_lookup, solver_lookup):
    """
    GIVEN a configured flask app and database
    WHEN calling the static method Solver.validate_user_solver() 
        with a test username and solver name not associated
        with each other.
    THEN check if the the returned value is True
    """
    assert Solver.validate_user_solver(
        username='a_user_2', solver_name='test_solver_1') == False


def test_update_stats(init_database, solver_lookup):
    """
    GIVEN a configured flask app, database, and solver, 
    WHEN calling the update_stats() method on a solver,
    THEN check if the solver's stats were updated.
    """
    solver_lookup.update_stats(True, 4)
    assert solver_lookup.words_played == 11
    assert solver_lookup.words_won == 9
    assert solver_lookup.avg == 81.82
    assert solver_lookup.current_streak == 6
    assert solver_lookup.max_streak == 6


def test_reset_solver_games(init_database, solver_lookup):
    """
    GIVEN a configured flask app, database, and solver, 
    WHEN calling the reset_solver method on a solver
    THEN check if the solver's stats were zeroed out and
        that the games linked to this solver were deleted 
        from the database.
    """
    solver_lookup.reset_games()
    assert solver_lookup.words_played == 0
    assert solver_lookup.words_won == 0
    assert solver_lookup.avg == 0
    assert solver_lookup.avg_guesses is None
    assert solver_lookup.max_streak == 0
    assert solver_lookup.current_streak == 0

    # Testing the games
    game_count = db.session.scalar((
                            db.select(func.count(Game.id)).where(
                            Game.solver_id == solver_lookup.id)
                            ))
    assert game_count == 0


def test_get_solver_games(init_database, preload_solver):
    """
    GIVEN a configured flask app, database, and solver
        with a game row in the Game table
    WHEN calling the solver's get_games() method with "won", "lost",
        and "None"
    THEN checking if the query returned is correct
    """

    games_query = preload_solver.get_games()
    games = list(db.session.scalars(games_query))
    assert len(games) == 1


#====================================================================
# Game Model Tests
#====================================================================
def test_add_game(init_database, solver_lookup):
    """
    GIVEN an initialized database and solver instance,
    WHEN creating and committing new Game instance with the solver_lookup.id, 
    THEN searching for and asserting that the game was added to the database.
    """
    new_game = Game(
            solver_id = solver_lookup.id,
            correct_word = 'corgi'
    )
    db.session.add(new_game)
    db.session.commit()

    game_row = db.session.scalar(db.select(Game).where(and_(Game.solver_id == solver_lookup.id, Game.correct_word == 'corgi')))
    assert game_row != None
    assert game_row.solver_id == solver_lookup.id


def test_update_game(init_database, active_game):
    """
    GIVEN an initialized database and active game instance,
    WHEN calling the update_game() class method with a guess and feedback on the game instance, 
    THEN checking if the game row instance was updated correctly.
    """
    active_game.update_game(guess="tests", feedback="BBYBB")
    assert active_game.guess_count == 1
    assert active_game.status == True
    assert active_game.guesses == "tests"
    assert active_game.feedback == "BBYBB"


def test_get_token(init_database, active_game):
    """
    Tests both the get_token() and check_toke() methods

    GIVEN a database and active game row instance,
    WHEN creating a new token using the get_token() method
    THEN check if check_token() static method with the token 
        as an argument returns True
    """
    assert active_game.token is None
    active_game.get_token()
    assert Game.check_token(active_game.token) == True


def test_game_payload_with_correct_word(init_database, active_game):
    """
    GIVEN a database and active game row instance,
    WHEN calling the create_payload method with include_correct=True,
    THEN check if the payload is correct
    """
    payload = active_game.create_payload(include_correct=True)
    assert payload['game_id'] == active_game.id
    assert payload['correct_word'] == 'flask'
    assert payload['status'] == True


def test_game_payload_without_correct_word(init_database, active_game):
    """
    GIVEN a database and active game row instance,
    WHEN calling the create_payload method with include_correct=False,
    THEN check if the payload is correct
    """
    payload = active_game.create_payload(include_correct=False)
    assert payload['game_id'] == active_game.id
    assert payload['correct_word'] == '*****'
    assert payload['status'] == True


def test_game_payload_with_feedback(init_database, active_game_2):
    """
    GIVEN a database and active game row instance,
    WHEN calling the create_payload method with include_feedback=True,
    THEN check if the payload is correct
    """
    
    payload = active_game_2.create_payload(include_feedback=True)
    assert payload["guesses"] == {
                            1: {"guess": "tests", "feedback": "YYBBB"}, 
                            2: {"guess": "corgi", "feedback": "BBYYB"}
                        }


def test_game_payload_without_feedback(init_database, active_game_2):
    """
    GIVEN a database and active game row instance,
    WHEN calling the create_payload method with include_feedback=False,
    THEN check that the payload doesn't have the guesses key
    """
    
    payload = active_game_2.create_payload(include_feedback=False)
    assert payload["guesses"] == {}
  

def test_game_payload_with_message(init_database, active_game_2):
    """
    GIVEN a database and active game row instance,
    WHEN calling the create_payload method with a message,
    THEN check that the payload contains the given message
    """
    
    payload = active_game_2.create_payload(message='Word not found in our dictionary.')
    assert payload["message"] == 'Word not found in our dictionary.'