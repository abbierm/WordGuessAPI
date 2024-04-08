from app import db
from app.models import User, Solver, Game

# testing the sqlalchemy models outside the flask app context


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
    assert user.is_authenticated
    assert user.is_active
    assert not user.is_anonymous



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


def test_add_solver(new_user):
    """
    GIVEN a User model and new user
    WHEN a solver is created
    THEN check if the solver.user_id is the same as the new users
    """
    new_solver = Solver(name='new_user_solver', user_id=new_user.id)
    assert new_solver.name == 'new_user_solver'
    assert new_solver.user_id == new_user.id
    

        
def test_add_game(new_user, new_solver):
    """
    Given a user and a solver
    Create a new game 
    Check the user_id and solver_id on game model
    """
    new_game = Game(user_id=new_user.id, solver_id=new_solver.id)
    assert new_game.user_id == new_user.id
    assert new_game.solver_id == new_solver.id
    

# TODO: test password hashing

# TODO: test user to_dict functions

# TODO: test game get token

# TODO: Test update game function

# TODO: Test creating payload 


