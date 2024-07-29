from collections import OrderedDict
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
from time import time
import secrets


MAX_SIZE = 50


class GameNode(BaseModel):
    game_token: Optional[str] = None
    token_expiration: Optional[datetime] = None
    solver_name: str
    solver_id: int
    user_id: int
    correct_word: str
    guess_count: int = 0
    guesses: str = ""
    feedback: str = ""
    status: bool = True
    results: Optional[bool] = None


def create_payload(
        game: GameNode, 
        include_feedback: bool = True, 
        include_correct: bool = True,
        message: Optional[str] = None
) -> dict:
    """
    Using this helper function rather than the model_dumps() via pydantic
    because some fields are included/excluded depending on which stage in the
    gameplay loop this payload is being created 
    """
    payload = {
        "game_token": game.game_token,
        "solver_name": game.solver_name,
        "correct_word": "*****",
        "status": game.status,
        "guess_count": game.guess_count,
        "guesses": {},
        "message": str(message),
        "results": "None"
    }
    if include_feedback == True:
        feedback_dict = {}
        guess_list = game.guesses.split(', ')
        feedback_list = game.feedback.split(', ')
        for i in range(len(guess_list)):
            feedback_dict[i + 1] = {
                "guess": guess_list[i], 
                "feedback": feedback_list[i]
            }
        payload["guesses"] = feedback_dict
    if include_correct == True:
        payload["correct_word"] = game.correct_word
        if game.results == True:
            payload["results"] = "won"
        else:
            payload["results"] = "lost"
    return payload


def update_game(
        game: GameNode,
        guess: str,
        feedback: str
):
    game.guess_count += 1
    if game.guess_count == 1:
        game.feedback = feedback
        game.guesses = guess
    else:
        game.feedback = "%s, %s" % (game.feedback, feedback)
        game.guesses = "%s, %s" % (game.guesses, guess)
    if feedback == "GGGGG":
        game.status = False
        game.results = True
    elif game.guess_count == 6:
        game.status = False
        game.results = False


class GameCache:
    """
    Stores Game rows in the form of pydantic models until
    game is completed to reduce the number of db calls.

    This is a LRU cache where the front of the 
    list is effectively the last item accessed. 
    
    GameNodes get removed either when the game 
    finishes or if the cache is at max capacity
    of 50 in which case the item in the front 
    of the list will get popped().
    """

    def __init__(
        self, 
        app=None, 
        capacity: int=MAX_SIZE
    ):
        if app is not None:
            self.init_app(app)
        self.capacity = capacity
        self.cache = OrderedDict()
        self.current_size = 0

    def init_app(self, app):
        self.app=app 
    
    # TODO: Self policing cache retrieval

    @staticmethod
    def make_token():
        token = secrets.token_hex(16)
        return token

    def check_expiration(game: GameNode):
        pass

    def get(self, api_key: str) -> GameNode:
        try:
            game = self.cache[api_key]
            self.cache.move_to_end(api_key)
            return game
        except KeyError:
            return None

    def put(self, game_node: GameNode):
        if self.current_size == self.capacity:
            self.cache.popitem(last=False)
        self.cache[game_node.game_token] = game_node
        self.cache.move_to_end(game_node.game_token)
        self.current_size += 1
       

    def remove(self, api_key):
        if api_key in self.cache:
            self.cache.popitem(api_key)
            self.current_size -= 1
