"""
Tests the database function's individually inside of the application scope.

"""

from app import db
from app.models import User, Game, Solver
from sqlalchemy import exc
import sqlalchemy as sa


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
    WHEN adding and commiting a new user with the same name as another user
    THEN check if sqlalchemy error occures
    """
    def check_adding_user() -> bool:
        try:
            new_user = User(username='test_user_3', email='atestingemail@gmail.com')
            new_user.set_password('password')
            db.session.add(new_user)
            db.session.commit()
            return True
        except exc.SQLAlchemyError:
            return False
    
    result = check_adding_user()
    assert result == False





# TODO: Test duplicate email


#TODO: 
# def test_get_token(init_database):

# TODO:
# def test_check_game_token(init_database):