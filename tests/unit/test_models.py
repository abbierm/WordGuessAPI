from app import db
from app.models import User, Solver, Game

# testing the sqlalchemy models outside the flask app context


def test_adding_user():
    """
    Creating a new User
    then check the username

    # TODO: After adding authentication will need to add password, email, etc. 
    """
    user = User(username='a_new_user')
    assert user.username == 'a_new_user'



def test_new_user_with_fixture(new_user):
    """
    Using pytest fixture checking if the new user has the correct username.

    # TODO: Once authentication is added will need to update this and the conftest file for password and email.
    """

    assert new_user.username == 'a_cool_username'



def test_add_solver(new_user):
    """
    Adding a new solver to the new_user text fixture and testing solver methods.
    """
    u_id = new_user.id
    new_solver = Solver(name='new_user_solver', user_id=u_id)
    assert new_solver.name == 'new_user_solver'
    assert new_solver.user_id == u_id
    
    

        
def test_add_game(new_user, new_solver):
    """
    Given a user and a solver
    Create a new game 
    Check the user_id and solver_id on game model
    """
    new_game = Game(user_id=new_user.id, solver_id=new_solver.id)
    assert new_game.user_id == new_user.id
    assert new_game.solver_id == new_solver.id
    