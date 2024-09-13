from pydantic import BaseModel
import random
import re
import requests
import sys
from typing import Dict, Optional
from words.correct import correct_words
from requests.auth import HTTPBasicAuth
import keyring


START_URL = 'http://127.0.0.1:5000/api/start'
GUESS_URL = 'http://127.0.0.1:5000/api/guess'
TOKEN_URL = 'http://127.0.0.1:5000/api/tokens'

#=======================================================
#    Pydantic Models
#=======================================================
class GuessFeedback(BaseModel):
    guess: str
    feedback: str

class GameData(BaseModel):
    game_token: str
    solver_name: str
    status: bool = True
    guess_count: int
    guesses: Optional[Dict[int, GuessFeedback]] = None
    correct_word: str
    message: str
    results: Optional[str] = None
    
    
class Guess(BaseModel):
    game_token: str
    guess: str
    

#===============================================================
#    Regex Solver Class
#===============================================================
class RegexSolver:
    def __init__(self, username: str):
        self.username = username
        self.rounds: int = None
        self.api_password = keyring.get_password("regex", self.username)
        self.solver_id = keyring.get_password("solver_id", self.username)

        # API 
        self.api_token = None
        self.game_token = None
        self.status: bool = True
        self.current_guess = None
        self.token_header = {"Authorization": None}
        self.start_payload = {"solver_id": self.solver_id}
        self.guess_payload = {}

        # Helpers to pick next word
        self.words = None
        self.guess_count = 0
        self.feedback: None
        self.all_yellow = []
        self.grey_letters = [0, 1, 2, 3, 4]
        self.constructed_word = [0, 1, 2, 3, 4]
        self.yellow_letters = [0, 1, 2, 3, 4]
        self.regex_pattern_list = [0, 1, 2, 3, 4]
        self.regex_pattern = None
        self.current_result: Optional[str] = None
        
        # Stores total game data
        self.total_played = 0
        self.wins: int = 0
        self.losses: int = 0
        self.average_wins: float = None
        self.average_guesses: float = None
        self.total_guesses: int = 0


#===============================================================
#    Helpers
#===============================================================
    def _populate_words(self):
        self.words = set(correct_words[:])

    def _reset_helpers(self):
        self.all_yellow = set()
        self.grey_letters = [0, 1, 2, 3, 4]
        self.constructed_word = [0, 1, 2, 3, 4]
        self.yellow_letters = [0, 1, 2, 3, 4]
        self.regex_pattern_list = [0, 1, 2, 3, 4]
        self.status = True
        self.feedback = None
        self.regex_pattern = ''
        self.guess_count = 0
        self.current_guess = None
        self.current_result = None
        
    
#===============================================================
#    Uses Feedback to pick the next word
#===============================================================
    def _parse_regex_pattern(self, letter: str, index: int, valid=True):
        """
        Inserts new letter's pattern into the existing word. 
        
        valid = "({letter})? | "
        invalid = "[^other letters{letter}]        
        """
        pattern = self.regex_pattern_list[index]
        
        if valid is True:
            self.regex_pattern_list[index] = f"[{letter}]"
        else:
            if isinstance(pattern, int):
                self.regex_pattern_list[index] = f"[^{letter}]"
            else:
                start = pattern.find("[^")
                if start == -1:
                    self.regex_pattern_list[index] = pattern + f"[^{letter}]"
                else:
                    end = pattern.find("]", start)
                    new = pattern[:end] + letter + pattern[end:]
                    self.regex_pattern_list[index] = new
        
                    
    def _create_green_pattern(self):
        """Adds the letter to the correct spot. """
        for i, letter in enumerate(self.constructed_word):
            if isinstance(letter, str):
                self._parse_regex_pattern(letter, i)


    def _create_yellow_pattern(self):
        for i, letter in enumerate(self.yellow_letters):
            if isinstance(letter, str):
                self._parse_regex_pattern(letter, i, valid=False)
                    
    
    def _create_grey_pattern(self):
        for i, letter in enumerate(self.grey_letters):
            if isinstance(letter, str):
                if letter in self.yellow_letters:
                    # Just adding it to that one spot
                    self._parse_regex_pattern(letter, i, valid=False)
                else:
                    for j in range(len(self.regex_pattern_list)):
                        if isinstance(self.constructed_word[j], int):
                            self._parse_regex_pattern(letter, j, valid=False)
        

    def _make_regex_pattern(self):
        # Updates green, yellow, and grey lists        
        for i, color in enumerate(self.feedback):
            letter = self.current_guess[i]
            if color == "G":
                self.constructed_word[i] = letter
            elif color == 'Y':
                self.yellow_letters[i] = letter
                self.all_yellow.add(letter)
            else:
                self.grey_letters[i] = letter

        self._create_green_pattern()
        self._create_yellow_pattern()
        self._create_grey_pattern()

        # adding '\\w' to the spots with any integers
        the_end_pattern = ['\\w' if isinstance(thing, int) == True else thing for thing in self.regex_pattern_list]
        self.regex_pattern = ''.join(the_end_pattern)
        

    def _filter_words(self):
        filtered_list = list(filter(lambda v: re.match(self.regex_pattern, v), self.words))
        self.words = filtered_list
        
          
    def _pick_best_first_word(self) -> str:
        # "Good" first wordle word choices?
        the_best_list = ['aisle', 'anime', 'ghost', 'roast', 'resin', 'tares', 'soare', 'raise', 'seare', 'crate']
        return random.choice(the_best_list)


    def _check_for_yellows(self, choice) -> bool:
        for i in self.all_yellow:
            if i not in choice:
                return False
        return True


    def _choose(self) -> str:
        while True:
            choice = random.choice(self.words)
            if self._check_for_yellows(choice) == True:
                return choice


    def _reset_lists(self):
        """Resets the grey and yellow lists."""
        self.yellow_letters = [0, 1, 2, 3, 4]
        self.grey_letters = [0, 1, 2, 3, 4]


    def _pick_next_word(self):
        if self.guess_count == 0:
            self.current_guess = self._pick_best_first_word()
        else:
            self._make_regex_pattern()
            self._filter_words()
            if len(self.words) == 0:
                self.current_guess = 'loser'
            else:
                self.current_guess = self._choose()
         

#==============================================================
#    api 
#==============================================================
    def _request_token(self):
        basic_auth = HTTPBasicAuth(
                self.username, 
                self.api_password
            )
        try:
            token_request = requests.post(
                url=TOKEN_URL, auth=basic_auth
            )
            self.api_token = token_request.json()["token"]
            self.token_header['Authorization'] = f"Bearer {self.api_token}"
        except (requests.JSONDecodeError, KeyError) as e:
            print(f"Request error: {e}")
            sys.exit()

    def _unload_response(self, payload: GameData):
        self.guess_count = payload.guess_count
        self.guesses = payload.guesses
        if self.guess_count != 0:
            self.feedback = self.guesses[self.guess_count].feedback
        else:
            self.game_token = payload.game_token
        self.status = payload.status
        if self.status == False:
            self.current_results = payload.results
        
        return


    def start(self):
        r = requests.post(
            url=START_URL,
            headers=self.token_header, 
            json=self.start_payload
        )
        try:
            x = r.json()
            start_response = GameData(**x)
            self._unload_response(start_response)

        except (TypeError, requests.JSONDecodeError) as e:
            print(f"Stat error: {e}")
            sys.exit()
    

    def guess(self) -> GameData:
        self.guess_payload = {
            "game_token": self.game_token,
            "guess": self.current_guess    
        }
        r = requests.post(
            url=GUESS_URL,
            json=self.guess_payload,
            headers=self.token_header
        )
        try:
            x = r.json()
            guess_response = GameData(**x)
            self._unload_response(guess_response)
        except requests.JSONDecodeError as e:
            print(f"Guess error: {e}")
            sys.exit()


#==============================================================
#    Updates Stats
#==============================================================
    def update_single_stats(self):
        self.total_played += 1
        if self.current_results == 'won':
            self.wins += 1
            self.total_guesses += self.guess_count
        else:
            self.losses += 1
        


#==============================================================
#    Gameplay loop
#===============================================================
    def _play_round(self):
        self.start()
        while self.guess_count < 6:
            self._reset_lists()
            self._pick_next_word()
            self.guess()
            if self.status == False:
                return


    def play(self, rounds: int):
        self.rounds = rounds
        count = 1
        # Request Token
        self._request_token()

        # Gameplay Loop
        while count <= self.rounds:
            self._populate_words()
            self._reset_helpers()
            self._play_round()
            self.update_single_stats()
            count += 1


#===============================================================
# Main Program Loop
#===============================================================
def main():
    solver_instance = RegexSolver(username='devUser')
    solver_instance.play(250)

if __name__ == "__main__":
    main()
