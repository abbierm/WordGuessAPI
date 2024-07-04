# Lookup routes to see current user and solver stats

from app import db
from app.api import bp
from app.api.errors import bad_request
from app.models import User, Solver, Game
from pydantic import BaseModel, ConfigDict, ValidationError
from app.wordguess import create_game, game_loop
from flask import request
import sqlalchemy as sa


# ==========================================================
# Gameplay model validation
# ==========================================================
class Start(BaseModel):
    model_config = ConfigDict(strict=True)
    solver_api_key: str
    user_id: int


class Guess(BaseModel):
    model_config = ConfigDict(strict=True)
    token: str
    game_id: int
    guess: str


#====================================================================
# Gameplay routes
#====================================================================
@bp.route('/start', methods=["POST"])
def start_game():
    data = request.get_json()
    # Validate that the POST body contains the correct information
    try:
        payload = Start.model_validate(data)
    except ValidationError:
        return bad_request("Invalid POST request. /start route must include a valid user id and the solver's unique api key Both of which can be obtained via the website.")

    # Check that solver token is valid and belongs to correct user
    solver = Solver.check_key(payload.solver_api_key)
    if solver is None or solver.user_id != payload.user_id:
        return bad_request("User id doesn't match id from solver_api key.  Check your user id and solve id via our website.")
    return create_game(solver.id)


@bp.route('/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    try:
        payload = Guess.model_validate(data)
    except ValidationError:
        return bad_request('Invalid guess.')
    token, game_id, guess = payload.token, payload.game_id, payload.guess
    
    if Game.check_token(token) == False:
        return bad_request('Invalid game-token, either game is expired or non-existent.')
    response = game_loop(game_id, guess)
    return response


#====================================================================
# api lookups to pull information from database
#====================================================================
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

# TODO: Add lookup for ALL the games data