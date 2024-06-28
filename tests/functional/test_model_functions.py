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

def test_adding_user(init_database):
    """
    GIVEN pre-filled database
    WHEN a new user is added to the database
    THEN check if user was added and found inside the db.
    """
    user = User(username='user5', email='u5@gmail.com')
    user.set_password('test_password')
    db.session.add(user)
    db.session.commit()
    user_lookup = db.session.scalar(
        db.select(User).where(
            User.username == 'user5'))
    assert user_lookup.username == 'user5'
    assert user_lookup.email == 'u5@gmail.com'
    
    
def test_adding_duplicate_usernames(init_database):
    """
    GIVEN a configured flask app and initialized database
    WHEN calling check_duplicate_username() with 'user1'
    THEN check if returns True
    """
    assert User.check_duplicate_username('user1') == True
    
def test_duplicate_email_check(init_database):
    """
    GIVEN a configured flask app and initialized db with registered users
    WHEN calling check_duplicate_email() with 'aTestEmail@email.com'
    THEN check if function returns True
    """   
    assert User.check_duplicate_email('u1@gmail.com') == True


def test_user_to_dict(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling to_dict() method for initialized user
    THEN check if returned payload is correct
    """
    user = db.session.scalar(db.select(User).where(User.id == 2))
    payload = user.to_dict()
    assert payload['id'] == 2
    assert payload['username'] == 'user2'
    assert payload['email'] == 'u2@gmail.com'
    assert payload['solvers'] == ['solver21', 'solver22']


def test_check_user_password(init_database):
    """
    GIVEN a configured flask app with testing database
    WHEN calling the User.check_password() function
    THEN check if it returns 'True' for the correct password
        and 'False' for the incorrect password. 
    """
    user = db.session.scalar(db.select(User).where(User.id == 2))
    assert user.check_password('test_password') == True
    assert user.check_password('not_a_test_password') == False


def test_generate_confirmation_token(init_database):
    """
    GIVEN a configured flask app with a testing database
    WHEN calling the User.generate_confirmation_token 
    THEN check if the verify_account returns 'True' for correct
        user
    """
    user = db.session.scalar(db.select(User).where(User.id == 2))
    token = user.generate_confirmation_token()
    user_lookup = User.verify_account(token)
    assert user_lookup.id == user.id


def test_reset_password_token(init_database):
    """
    GIVEN a configured flask app with a testing database
    WHEN calling the get_reset_password_token on a user instance
    THEN checking if the verify_reset_password_token() function works
    """
    user = db.session.scalar(db.select(User).where(User.id == 2))
    reset_token = user.get_reset_password_token()
    returned_user = User.verify_reset_password_token(reset_token)
    assert user.id == returned_user.id


# #====================================================================
# # Solver Model Tests
# #==================================================================== 
def test_adding_new_solver(init_database):
    """
    GIVEN a configured flask app and testing database,
    WHEN adding a new solver to a user instance,
    THEN check if the solver is added and committed to the 
        database by doing a solver query lookup.
    """
    
    new_solver = Solver(user_id=3, name='corgi_solver')
    db.session.add(new_solver)
    db.session.commit()
    solver = db.session.scalar(db.select(Solver).where(Solver.name == 'corgi_solver'))
    assert solver.user_id == 3
    assert solver.name == 'corgi_solver'


def test_solver_to_dict(init_database):
    """
    GIVEN a configured flask app, database
    WHEN calling the to_dict() method on a solver instance
    THEN check if if the information is correct.
    """
    solver = db.session.scalar(db.select(Solver).where(Solver.id == 2))
    payload = solver.to_dict()
    assert payload["id"] == 2
    assert payload["name"] == 'solver21'
    assert payload["user_id"] == 2
    assert payload["words_played"] == 10
    assert payload["words_won"] == 8
    assert payload["avg_won"] == 80
    assert payload["avg_guesses"] == 4.5
    assert payload["max_streak"] == 5
    assert payload["api_key"] =='bd64d06a6d271e3a9254afd0e7a94977'


def test_make_solver_api_key(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling the make_api() method on a solver instance
    THEN check if API key was created in the correct format
    """
    solver = db.session.scalar(db.select(Solver).where(Solver.id == 2))
    solver.make_api_key()
    assert solver.api_key != 'bd64d06a6d271e3a9254afd0e7a94977'
    assert type(solver.api_key) == str
    assert len(solver.api_key) == 32


def test_check_api_key(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling the check_api() static method with a valid API key
    THEN check if the returned solver is correct
    """
    solver = Solver.check_key('bd64d06a6d271e3a9254afd0e7a94978')
    assert solver.name == 'solver22'


def test_check_api_key_incorrect(init_database):
    """
    GIVEN a configured flask app, database
    WHEN calling the Solver.check_api() static method 
        using a incorrect key
    THEN check if the solver returned from check_key 
        is None
    """
    solver = Solver.check_key('bd64d06a6d271e3a9254afd0e7a94975')
    assert solver is None


def test_validate_user_solver_true(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling the static method Solver.validate_user_solver() 
        with a test username and solver name associated with
        that user
    THEN check if the the returned value is True
    """
    assert Solver.validate_user_solver(
        username='user2', solver_name='solver21') == True


def test_validate_user_solver_false(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling the static method Solver.validate_user_solver() 
        with a test username and solver name not associated
        with each other.
    THEN check if the the returned value is True
    """
    assert Solver.validate_user_solver(
        username='user1', solver_name='solver21') == False


def test_update_stats(init_database):
    """
    GIVEN a configured flask app, database, and solver, 
    WHEN calling the update_stats() method on a solver,
    THEN check if the solver's stats were updated.
    """
    solver = db.session.scalar(db.select(Solver).where(Solver.id == 2))
    solver.update_stats(True, 4)
    assert solver.words_played == 11
    assert solver.words_won == 9
    assert solver.avg == 81.82
    assert solver.current_streak == 6
    assert solver.max_streak == 6


def test_reset_solver_games(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling the reset_solver method on a solver
    THEN check if the solver's stats were zeroed out and
        that the games linked to this solver were deleted 
        from the database.
    """
    solver = db.session.scalar(db.select(Solver).where(Solver.id == 2))
    solver.reset_games()
    assert solver.words_played == 0
    assert solver.words_won == 0
    assert solver.avg == 0
    assert solver.avg_guesses is None
    assert solver.max_streak == 0
    assert solver.current_streak == 0

    # Testing the games
    game_count = db.session.scalar((
                            db.select(func.count(Game.id)).where(
                            Game.solver_id == 2)
                            ))
    assert game_count == 0


def test_get_solver_games_won(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling a solver instance get_games() method with "won"
    THEN checking if the query returned is correct
    """
    solver = db.session.scalar(db.select(Solver).where(Solver.id == 4))
    games_query = solver.get_games(filter="won")
    games_list = list(db.session.scalars(games_query))
    assert len(games_list) == 1

    
def test_get_solver_games(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling a solver instance get_games() method with no filter
    THEN checking if the query returned is correct
    """
    solver = db.session.scalar(db.select(Solver).where(Solver.id == 4))
    games_query = solver.get_games()
    games_list = list(db.session.scalars(games_query))
    assert len(games_list) == 2

def test_get_solver_games_lost(init_database):
    """
    GIVEN a configured flask app and database
    WHEN calling a solver instance get_games() method with "lost"
    THEN checking if the query returned is correct
    """
    solver = db.session.scalar(db.select(Solver).where(Solver.id == 4))
    games_query = solver.get_games(filter="lost")
    games_list = list(db.session.scalars(games_query))
    assert len(games_list) == 1

# #====================================================================
# # Game Model Tests
# #====================================================================
def test_add_game(init_database):
    """
    GIVEN an initialized flask app and solver instance
    WHEN creating and committing new Game instance with a valid solver id 
    THEN searching for and asserting that the game was added to the database.
    """
    new_game = Game(
            solver_id = 2,
            correct_word = 'knead',
    )
    db.session.add(new_game)
    db.session.commit()

    game_row = db.session.scalar(db.select(Game).where(Game.id == new_game.id))
    assert game_row != None
    assert game_row.solver_id == 2


def test_update_game(init_database):
    """
    GIVEN an initialized flask app and filled database
    WHEN calling the update_game() class method with a guess and feedback on the game instance, 
    THEN checking if the game row instance was updated correctly.
    """
    new_game = Game(solver_id=2, correct_word='hello')
    db.session.add(new_game)
    db.session.commit()
    new_game.update_game(guess="anime", feedback="BBBBY")
    assert new_game.guess_count == 1
    assert new_game.guesses == "anime"
    assert new_game.feedback == "BBBBY"


def test_get_token(init_database):
    """
    Tests both the get_token() and check_toke() methods

    GIVEN a flask app and initialized filled db,
    WHEN creating a new token using the get_token() method
    THEN check if check_token() static method with the token 
        as an argument returns True
    """
    active_game = Game(solver_id=2, correct_word='model')
    db.session.add(active_game)
    db.session.commit()
    active_game.get_token()
    assert Game.check_token(active_game.token) == True


def test_get_payload_no_arguments(init_database):
    """
    GIVEN a initialized flask app with a filled db,
    WHEN calling the create_payload method without arguments
    THEN check if the payload contains all of the desired information
    """
    game = db.session.get(Game, 4)
    payload = game.create_payload()
    assert payload['game_id'] == 4
    assert payload['token'] == None
    assert payload['solver_id'] == 4
    assert payload['status'] == False
    assert payload['guess_count'] == 5
    assert payload['guesses'] == {}
    assert payload['correct_word'] == '*****'
    assert payload['message'] == 'None'
    assert payload['results'] ==  'None'


def test_game_payload_with_correct_word(init_database):
    """
    GIVEN a initialized flask app with a filled db,
    WHEN calling the create_payload method with a game row using the
        'include_correct'=True
    THEN check if the payload contains the correct information
    """
    game = db.session.get(Game, 4)
    payload = game.create_payload(include_correct=True)
    assert payload['game_id'] == 4
    assert payload['correct_word'] == 'beats'


def test_game_payload_without_correct_word(init_database):
    """
    GIVEN initialized flask app and filled db,
    WHEN calling the create_payload method on a game row instance
        setting the 'include_correct' argument to False
    THEN check if the payload doesn't contain the correct word
    """
    game = db.session.get(Game, 4)
    payload = game.create_payload(include_correct=False)
    assert payload['game_id'] == 4
    assert payload['correct_word'] == '*****'
    

def test_game_payload_with_feedback(init_database):
    """
    GIVEN initialized flask app and filled db,
    WHEN calling the create_payload method on a game row instance
        setting the 'include_feedback' argument to True
    THEN check if the payload contains the correctly formatted guesses
    """
    game = db.session.get(Game, 4)
    payload = game.create_payload(include_feedback=True)
    assert payload["guesses"] == {
                            1: {"guess": "tests", "feedback": "BGBGG"}, 
                            2: {"guess": "corgi", "feedback": "BBBBB"},
                            3: {"guess": "flask", "feedback": "BBGYB"},
                            4: {"guess": "ghost", "feedback": "BBBYY"},
                            5: {"guess": "beats", "feedback": "GGGGG"}
                        }


def test_game_payload_with_message(init_database):
    """
    GIVEN an initialized flask app and database,
    WHEN calling the create_payload method with a message on a game,
    THEN check that the payload contains the given message
    """
    game = db.session.get(Game, 4)
    payload = game.create_payload(message='Word not found in our dictionary.')
    assert payload["message"] == 'Word not found in our dictionary.'
    assert payload["game_id"] == 4