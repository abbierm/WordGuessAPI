# Lookup routes to see current user and solver stats

from app import db
from app.api import bp
from app.api.errors import bad_request
from app.api.auth import token_auth
from app.models import Solver, Game
from app.wordguess import create_game, game_loop
from flask import request
import sqlalchemy as sa
from pydantic import BaseModel, ValidationError, ConfigDict


class Start(BaseModel):
    model_config = ConfigDict(strict=True)
    solver_id: str

class Guess(BaseModel):
    model_config = ConfigDict(strict=True)
    game_token: str
    guess: str


#===============================================================
# Gameplay routes
#===============================================================
@bp.route('/start', methods=["POST"])
@token_auth.login_required
def start_game():
    json_data = request.get_json()
    user = token_auth.current_user()
    
    # Makes sure that the starting payload only contains necessary data
    try:
        start_data = Start.model_validate(json_data)
    except ValidationError as e:
        print(e)
        return bad_request("Invalid starting payload. Form data should only contain the solver_id for the solver you want to play wordguess with.")
    
    # Checks that solver id matches a solver in db and 
    # solver matches the user's token auth credentials
    solver = Solver.check_api_id(start_data.solver_id)
    if not solver or user.id != solver.user_id:
        return bad_request("Invalid solver_id.")

    # Creates new game in wordguess.py file and returns starting payload
    starting_game_payload = create_game(user_id=user.id,  solver_id=solver.id)
    return starting_game_payload
    

@bp.route('/guess', methods=['POST'])
@token_auth.login_required
def make_guess():
    json_data = request.get_json()
    user = token_auth.current_user()

    try:
        guess_data = Guess.model_validate(json_data)
    except ValidationError:
        return bad_request("Invalid guess payload. \
            Form data should be sent in json and only contain the unique game_token and the guess for the game ")

    game = Game.check_game_token(guess_data.game_token)
    if not game or user.id != game.user_id:
        return bad_request("Invalid game_token")
    return game_loop(game_id=game.id, guess=guess_data.guess)


#====================================================================
# api lookups to pull information from database
#====================================================================
@bp.route('/lookup_solver/<string:solver_name>', methods=["GET"])
@token_auth.login_required
def lookup_solver(solver_name):
    solver = db.session.scalar(db.select(Solver).where(Solver.name == solver_name))
    if solver is None:
        return bad_request(f'Unable to find solver with the name {solver_name}')
    payload = solver.to_dict()
    return payload


@bp.route('/lookup_games/<string:solver_name>', methods=["GET"])
@token_auth.login_required
def get_games(solver_name):
    solver = db.session.scalar(db.select(
                                    Solver).where(Solver.name == solver_name))
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    return Game.to_collection_dict(
        sa.select(Game).where(Game.solver_id == solver.id), 
        page, per_page, 'api.get_games')
