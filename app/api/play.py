from flask import request, url_for, jsonify
from app.wordguess import GAMES, make_game, game_loop
from app.api import bp

from app.api.errors import bad_request



@bp.route('/start/<string:username>')
def start_game(username):
    # Returns api_game_id
    game_id = make_game(username)

    return {"game_id": game_id}



@bp.route('/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    print(data)
    if 'game_id' not in data or 'guess' not in data:
        return bad_request('must include game id and the next guess')
    game_id, guess = data["game_id"], data["guess"]

    try:
        game_id = int(game_id)
        GAMES[game_id]
        
    except (KeyError):
        return bad_request('Game id is not a valid number.')

    response = game_loop(game_id, guess)
    print(response)
    return response


 
"""Guess via GET response."""
# @bp.route('/guess/<int:id>/<string:guess>')
# def make_guess(id: int, guess: str):
#     try:
#         game_id = int(id)
#         GAMES[id]
#         print(GAMES[id])
#     except(ValueError, KeyError):
#         return bad_request('Game id is not valid.')
#     response = game_loop(game_id, guess)
#     return response
