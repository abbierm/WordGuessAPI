from pydantic import BaseModel
import random
import re
import requests
import sys
from typing import Dict, Optional
from words.correct import correct_words
from requests.auth import HTTPBasicAuth

# This is API key used for testing 
# and will not work in production
SOLVER_ID = 'd8297cca990daf3f0e8b031ccd02c02a'
START_URL = 'http://127.0.0.1:5000/api/start'
GUESS_URL = 'http://127.0.0.1:5000/api/guess'
TOKEN_URL = 'http://127.0.0.1:5000/api/tokens'
BASIC_AUTH = HTTPBasicAuth("devUser", "test_password")



#=======================================================
#    Pydantic Models
#=======================================================
class GuessFeedback(BaseModel):
    guess: str
    feedback: str

class GameData(BaseModel):
    game_token: int
    solver_name: str
    status: bool = True
    guess_count: int
    status: bool = True
    guess_count: int
    guesses: Optional[Dict[int, GuessFeedback]] = None
    correct_word: str
    message: str
    results: Optional[str] = None
    
    
class Guess(BaseModel):
    game_token: str
    guess: str
    

#==========================================================================
#    Regex Solver Class
#==========================================================================
class RegexSolver:
    def __init__(self, username: str):
        self.username = username
        self.rounds: int = None
        self.api_token = None

        # API 
        self.token: Optional[str] = None
        self.status: bool = True

        # Helpers to pick next word
        self.words = None
        self.current_guess = None
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


#==========================================================================
#    Resets for each new game
#==========================================================================
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
        
    
#==========================================================================
#    Uses Feedback to pick the next word
#==========================================================================
    def _parse_regex_pattern(self, letter: str, index: int, valid=True):
        """
        Inserts new letter's pattern into the exsisting word. 
        
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
        logger.debug("New Pattern: %s from feedback: %s", self.regex_pattern, self.feedback)
        

    def _filter_words(self):
        filtered_list = list(filter(lambda v: re.match(self.regex_pattern, v), self.words))
        self.words = filtered_list
        
          
    def _pick_best_first_word(self) -> str:
        # "Good" first wordle word choices?
        the_best_list = ['aisle', 'anime', 'ghost', 'roast', 'resin', 'tares', 'soare', 'raise', 'seare', 'roate']
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


    def pick_next_word(self):
        if self.guess_count == 0:
            self.current_guess = self._pick_best_first_word()
        else:
            self._make_regex_pattern()
            self._filter_words()
            if len(self.words) == 0:
                self.current_guess = 'loser'
            else:
                self.current_guess = self._choose()
         

#==========================================================================
#    api 
#==========================================================================
    # TODO: request token

    # TODO: create header
    
    def _unload_starting_payload(self, payload: GameData):
        self.token = payload.token
        self.game_id = payload.game_id
    

    def _unload_payload(self, payload: GameData):
        """
        Updates guess counts, current feedback and reports current status to the game-loop for flow control. 
        """
        self.guess_count = payload.guess_count
        self.guesses = payload.guesses
        self.feedback = self.guesses[self.guess_count].feedback
        self.status = payload.status
        if self.status == False:
            logger.info("End Of Game Guesses: %s", self.guesses)
            self.current_results = payload.results


    def start(self, url=START_URL) -> GameData:
        payload = {'solver_api_key': self.api_key, 'user_id': self.user_id}
        r = requests.post(url=url, json=payload)
        try:
            x = r.json()
            start_payload = GameData(**x)
            self._unload_starting_payload(start_payload)
        except (TypeError, requests.JSONDecodeError):
            logger.info("Starting payload error: %s", r.text)
            sys.exit()
    

    def guess(self) -> GameData:
        url = 'http://127.0.0.1:5000/api/guess'
        payload = {"token": self.token, "game_id": self.game_id, "guess": self.current_guess}
        r = requests.post(url, json=payload)
        try:
            x = r.json()
            payload = GameData(**x)
            return payload
        except requests.JSONDecodeError as e:
            print(e)
            sys.exit()


#==========================================================================
#    Updates Stats
#==========================================================================
    def update_single_stats(self):
        self.total_played += 1
        if self.current_results == 'won':
            self.wins += 1
            self.total_guesses += self.guess_count
        else:
            self.losses += 1
        


#==========================================================================
#    Gameplay loop
#==========================================================================
    def _play_round(self):
        self.start()
        while self.guess_count < 6:
            self._reset_lists()
            self.pick_next_word()
            payload = self.guess()
            self._unload_payload(payload)
            if self.status == False:
                return


    def play(self, rounds: int):
        self.rounds = rounds
        count = 1

        # Request Token
        try:
            token_request = requests.post(url=TOKEN_URL, auth=BASIC_AUTH)
            self.token = token_request.json()["token"]
        except requests.JSONDecodeError as e:
            print(e)
            sys.exit()


             
        # Gameplay Loop
        while count <= self.rounds:
            self._populate_words()
            self._reset_helpers()
            self._play_round()
            self.update_single_stats()
            count += 1


#==========================================================================
# Main Program Loop
#==========================================================================
def main():
    solver_instance = RegexSolver(username='devUser')
    solver_instance.play(1000)

if __name__ == "__main__":
    main()
