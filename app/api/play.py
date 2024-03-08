from flask import request, url_for, jsonify
#from app.wordguess import create_game, game_loop, GAMES, create_guess_payload
from app.api import bp

from app.api.errors import bad_request

from app.models import User, Solver, Game
from pydantic import BaseModel, ConfigDict, ValidationError
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from app.wordguess_db import create_game, game_loop


class Guess(BaseModel):
    model_config = ConfigDict(strict=True)
    token: str
    id: int
    guess: str



# Simple non-password way to create games, users, and solvers. 
@bp.route('/start/<string:username>/<string:solver_name>', methods=["GET"])
def start_game(username, solver_name):
    # Checks for the User
    if User.validate_user(username) == False:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    else:
        user = db.session.scalars(db.select(User).filter_by(username=username))
    # Checks for Solver
    if not Solver.validate_solver(solver_name):
        solver = Solver(name=solver, user_id=user.id)
    else:
        # Checks to make sure solver is their solver.
        if Solver.validate_user_solver(username, solver) == False:
            return bad_request('solver\'s name has already been created by another user, please try again with a solver name. ')
    #Creates Game
    new_game = create_game(user.id, solver.id)
    return new_game


@bp.route('/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    try:
        payload = Guess.model_validation(data)
    except ValidationError:
        return bad_request('Invalid guess.')
    token, game_id, guess = payload.token, payload.id, payload.guess
    
    if Game.check_token(token) == False:
        return bad_request('Invalid game-token, either game is expired or non-exsistant.')
    
    """
    From this point any invalid guesses will be handled 
    with errors inside of the standard payload.
    """
    response = game_loop(game_id, guess)
    return response


# @bp.route('/lookup/<string:game_id>', methods=["GET"])
# def lookup(game_id):
#     """
#     Returns entire payload (all guesses)
#     If game is is over will return the correct word 
#     """
#     try:
#         game = GAMES[game_id]
#     except(KeyError):
#         return bad_request('game_id is invalid')
#     if game["status"] is False:
#         return game
#     else:
#         return create_guess_payload(game_id)

