from flask import request, url_for, jsonify
#from app.wordguess import create_game, game_loop, GAMES, create_guess_payload
from app import db
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
    game_id: int
    guess: str


# Simple non-password way to create games, users, and solvers. 
@bp.route('/start/<string:username>/<string:solver_name>', methods=["GET"])
def start_game(username, solver_name):
    # Checks for the User in the database
    if User.validate_user(username) == False:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    else:
        user = db.session.scalar(db.select(User).filter_by(
                                            username=username))

    # Checks for Solver
    try:
        solver = db.session.scalar(db.select(Solver).filter_by(
                                        name=solver_name))
        if Solver.validate_user_solver(username, solver.name) == False:
            return bad_request('solver name already in user by another user.  Please choose a different name.')
    except SQLAlchemyError:
        solver = Solver(name=solver_name, user_id=user.id)
        db.session.add(solver)
        db.session.commit()
   
    #Creates Game
    print('creating a new game')
    new_game = create_game(user.id, solver.id)
    return new_game


@bp.route('/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    try:
        payload = Guess.model_validate(data)
    except ValidationError:
        return bad_request('Invalid guess.')
    token, game_id, guess = payload.token, payload.game_id, payload.guess
    
    if Game.check_token(token) == False:
        return bad_request('Invalid game-token, either game is expired or non-exsistant.')
    
    """
    From this point any invalid guesses will be handled 
    with errors inside of the standard payload.
    """
    response = game_loop(game_id, guess)
    return response


