# Lookup routes to see current user and solver stats

from app import db, game_cache
from app.api import bp
from app.api.errors import bad_request
from app.api.auth import token_auth
from app.models import Solver, Game, User
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
        return bad_request("Invalid solver_id")

    # Creates new game in wordguess.py file and returns starting payload
    starting_game_payload = create_game(
            solver_id=solver.id, 
            solver_name=solver.name, 
            user_id=solver.user_id
    )
    return starting_game_payload
    

@bp.route('/guess', methods=['POST'])
def make_guess():
    json_data = request.get_json()
    try:
        guess_data = Guess.model_validate(json_data)
    except ValidationError:
        return bad_request("Invalid guess payload. \
            Form data should be sent in json and only contain the unique game_token and the guess for the game ")

    game = game_cache.get(guess_data.game_token)
    return game_loop(game, guess=guess_data.guess)


#====================================================================
# api lookups to pull information from database
#====================================================================
@bp.route('/lookup_solver/<string:solver_name>', methods=["GET"])
@token_auth.login_required
def lookup_solver(solver_name: str):
    """
        Looks up the solver and returns a Dictionary of the solver's stats

        Parsing the header manually (in the same way that the Flask_HTTPAuth
        library does) to get access to the user instance. 
        
        Yes this is redundant BUT it allows me to make sure user solver
        belongs to the authorized user. Also allows me to send solver_ids 
        via API calls without it being too incredibly insecure. 
    """
    token = request.headers.get('Authorization').split(None, 1)[1]
    user = User.check_token(token)
    solver = db.session.scalar(db.select(Solver).where(
                                        Solver.name == solver_name))
    if solver is None or user.id != solver.user_id:
        return bad_request(f'Unable to find solver with the name {solver_name}')
    payload = solver.to_dict()
    return payload


#====================================================================
# Edit solver information
#====================================================================
@bp.route('/create_solver_id/<string:solver_name>', methods=["POST"])
@token_auth.login_required
def create_solver_id(solver_name: str):
    token = request.headers.get('Authorization').split(None, 1)[1]
    user = User.check_token(token)
    solver = db.session.scalar(db.select(Solver).where(
                                    Solver.name == solver_name))
    if solver is None or user.id != solver.user_id:
        return bad_request(f"Unable to find solver with the name {solver_name}")
    solver.make_api_id()
    return solver.to_dict()