"""
Tests the database function's individually inside of the application scope.

"""

from app import db
from app.models import User, Game, Solver
from sqlalchemy import exc
import sqlalchemy as sa

#===============================================================================
# User Model Tests
def test_adding_user(new_user, init_database):
    """
    GIVEN a configured flask app and initialized database
    WHEN adding and commiting a new user to the database
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
    WHEN adding and commiting a new user to the database
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
    

def test_adding_duplicate_usernames(init_database):
    """
    GIVEN a configured flask app and initialized database
    WHEN calling check_duplicate_username() with 'a_user'
    THEN check if fn() returns True
    """
    assert User.check_duplicate_username('a_user') == True


def test_duplicate_email_check(init_database):
    """
    GIVEN a configured flask app and initialized db with registered users
    WHEN calling check_duplicate_email() with 'aTestEmail@email.com'
    THEN check if function returns True
    """
    assert User.check_duplicate_email('test_email_user1@gmail.com') == True


def test_user_to_dict(init_database, user_lookup):
    """
    GIVEN a configured flask app and database
    WHEN calling to_dict() method for initialized user with username 'a_user'
    THEN check if returned payload is correct
    """
    payload = user_lookup.to_dict()
    assert payload['id'] == 1
    assert payload['username'] == 'a_user'
    assert payload['email'] == 'test_email_user1@gmail.com'

# TODO: test password reset token

# TODO: test confirmation token

#=========================================================
# Solver Model Tests
#=========================================================

# TODO: Test solver.to_dict

# TODO: Test update stats

# TODO: test validate user_solver

#========================================================
# Game Model Tests
#========================================================
# TODO: Tests update game function

# TODO: test api game token

# TODO: Test Creating payload function