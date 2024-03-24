from flask import request
from app import db
from app.api import bp
from app.api.errors import bad_request
from app.models import User, Solver, Game
from pydantic import BaseModel, ConfigDict, ValidationError
from app.wordguess import create_game, game_loop



class Guess(BaseModel):
    model_config = ConfigDict(strict=True)
    token: str
    game_id: int
    guess: str


# Simple non-password way to create games, users, and solvers. 
@bp.route('/start/<string:username>/<string:solver_name>', methods=["GET"])
def start_game(username, solver_name):
    
    # Finds user or creates a new user
    user = db.session.scalar(db.select(User).where(User.username == username))
    if user is None:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    
    # Checks for Solver
    solver = db.session.scalar(db.select(Solver).where(
                                    Solver.name == solver_name))
        # If the solver exists but doesn't belong to that user
    if solver is None:
        solver = Solver(name=solver_name, user_id=user.id)
        db.session.add(solver)
        db.session.commit()
    else:
        if solver.validate_user_solver(username, solver.name) == False:
            return bad_request('solver name already in user by another user.  Please choose a different name.')
    
    # Creates the new Game
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
