from app import db
from app.api import bp
from app.api.errors import bad_request
from app.models import User, Solver, Game
from pydantic import BaseModel, ConfigDict, ValidationError
from app.wordguess import create_game, game_loop
from flask import request
import sqlalchemy as sa


class Start(BaseModel):
    model_config = ConfigDict(strict=True)
    solver_api_key: str
    user_id: int


class Guess(BaseModel):
    model_config = ConfigDict(strict=True)
    token: str
    game_id: int
    guess: str


# Simple non-password way to create games, users, and solvers. 
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
    if solver is None:
        return bad_request("Invalid solver key doesn't match any registered solvers. Please request a new API key from website.")
    if solver.user_id != payload.user_id:
        return bad_request("User id doesn't match id from solver_api key.  Check your user id and solve id via our website.")

    # Create a new game
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
    
    """
    From this point any invalid guesses will be handled 
    with errors inside of the standard payload.
    """
    response = game_loop(game_id, guess)
    return response
