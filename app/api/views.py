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
    print(payload)
    return payload