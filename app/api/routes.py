# Lookup routes to see current user and solver stats

from app import db
from app.api import bp
from app.api.errors import bad_request
from app.models import User, Solver, Game


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




    
    