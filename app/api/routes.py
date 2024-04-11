# Lookup routes to see current user and solver stats

from app import db
from app.api import bp
from app.api.errors import bad_request
from app.models import User, Solver, Game
from flask import request


@bp.route('/lookup_solver/<string:solver_name>', methods=["GET"])
def lookup_solver(solver_name):
    solver = db.session.scalar(db.select(Solver).where(Solver.name == solver_name))
    if solver is None:
        return bad_request(f'Unable to find solver with the name {solver_name}')
    payload = solver.to_dict()
    return payload



@bp.route('/lookup_user_solvers/<string:username>', methods=["GET"])
def lookup_user(username: str):
    """ Returns all the solver's and stats owned by specific username. """

    user = db.session.scalar(db.select(User).where(User.username == username))
    if user is None:
        return bad_request(f"Unable to find a user with the username: {username}")
    solvers = db.session.scalars(db.select(Solver).where(
            Solver.user_id == user.id))
    
    solvers_payload = {}
    solvers_payload["user"] = user.to_dict()
    solvers_payload["solvers"] = {}

    if not solvers:
        return solvers_payload
     
    for solver in solvers:
        solvers_payload["solvers"][solver.name] = solver.to_dict()
    return solvers_payload



@bp.route('/create_account', methods=["POST"])
def create_account():
    data = request.get_json()

    # Validate info before adding new user
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('Must include username, email, and password fields')
    if User.check_duplicate_username(data['username']) == True:
        return bad_request('Username already in use by another user, please try again with a different username')
    if User.check_duplicate_email(data['email']) == True:
        return bad_request('Email already associated with another account.')
    
    # Adds new user to the database
    new_user = User(username=data['username'], email=data['email'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return new_user.to_dict()

    