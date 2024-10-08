"""
Testing the sqlalchemy models outside the  
flask app context by creating class instances  
and making sure the methods word correctly
"""

from app.models import User, Solver, Game
import pytest


# =========================================================
# User Model Tests
# =========================================================

def test_adding_user():
    """
    Given a User model
    When a new User is created
    Then check username, email, password hashing
    AND check flask_login is_authenticated, is_active, and is_anonymous
 
    """
    user = User(username='a_new_user', email='testemail@email.com')
    user.set_password('insecurepassword')
    assert user.username == 'a_new_user'
    assert user.email == 'testemail@email.com'
    assert user.password_hash != 'a_new_user'
    

def test_new_user_with_fixture(new_user):
    """
    GIVEN a User model and new user
    WHEN a new user is created
    THEN check the email, username, password, 
    AND check flask_login is_authenticated, is_active, and is_anonymous
    """
    assert new_user.username == 'a_cool_username'
    assert new_user.email == 'aTestEmail@email.com'
    assert new_user.password_hash != 'insecurePassword'
    assert new_user.is_authenticated
    assert new_user.is_active 
    assert not new_user.is_anonymous

def test_password_hashing():
    """
    GIVEN a User database model
    CREATE a new User and set the password
    CHECK if password is hashed and can't be pulled up
    """
    new_user = User(
                username='passwordHashingUser', 
                email='testingEmail@test_email.com'
            )
    new_user.set_password('TestPassword2')
    assert new_user.password_hash != 'TestPassword2'
    assert new_user.check_password('TestPassword2') == True
    assert new_user.check_password('TestPassword1') == False

def test_user_to_dict(new_user):
    """
    GIVEN a new user and the User database model
    CALL the to_dict() method
    CHECK if returned dictionary is correct
    
        Since this is checking the model itself and the new_user isn't added to the testing database, the user won't have an id number since that is added incrementally upon committing the db session.
    """
    payload = new_user.to_dict()
    assert payload['username'] == 'a_cool_username'
    assert payload['email'] == 'aTestEmail@email.com'
    
# =========================================================
# Solver Model Tests
# =========================================================
def test_add_solver(new_user):
    """
    GIVEN a User model and new user
    WHEN a solver is created
    THEN check if the solver.user_id is the same as the new users
    """
    new_solver = Solver(name='new_user_solver', user_id=new_user.id)
    assert new_solver.name == 'new_user_solver'
    assert new_solver.user_id == new_user.id


def test_solver_to_dict(new_solver):
    """
    Given a Solver class instance
    When to_dict method is called
    then check if the payload has all of the correct data.
    """
    test_payload = new_solver.to_dict()
    assert test_payload["name"] == "word_guess_solver"
    assert test_payload["words_played"] == 0
    assert test_payload["words_won"] == 0


# =============================================================
# Game Model Tests
# =============================================================
def test_add_game(new_solver):
    """
    Given a new solver and a correct word
    Create a new game 
    Check the solver_id on game model
    """
    new_game = Game(solver_id=new_solver.id, correct_word="tests")
    assert new_game.solver_id == new_solver.id
    assert new_game.correct_word == "tests"