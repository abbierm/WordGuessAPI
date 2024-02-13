from flask import request, url_for, jsonify
from app.wordguess import create_game, game_loop, GAMES, create_guess_payload
from app.api import bp

from app.api.errors import bad_request



@bp.route('/start/<string:username>', methods=["GET"])
def start_game(username):
    game_id = create_game(username)
    return {"game_id": game_id}



@bp.route('/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    if 'game_id' not in data or 'guess' not in data:
        return bad_request('must include game_id and a guess')
    game_id, guess = data['game_id'], data['guess']
    response = game_loop(game_id, guess)
    return response


@bp.route('/lookup/<string:game_id>', methods=["GET"])
def lookup(game_id):
    """
    Returns entire payload (all guesses)
    If game is is over will return the correct word 
    """
    try:
        game = GAMES[game_id]
    except(KeyError):
        return bad_request('game_id is invalid')
    if game["status"] is False:
        return game
    else:
        return create_guess_payload(game_id)

