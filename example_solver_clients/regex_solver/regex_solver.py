from datetime import datetime, date
import logging
import os
from pathlib import Path
from pydantic import BaseModel
import random
import re
import requests
import sys
from typing import Dict, Optional
from words.correct import correct_words

API_KEY = 'ffcd6d31e2cb988b1cc631a3095cc2ba'
USER_ID = 1
START_URL = 'http://127.0.0.1:5000/api/start'
GUESS_URL = 'http://127.0.0.1:5000/api/guess'


#========================================================
#    Logging
#========================================================
THIS_DIRECTORY = os.path.dirname(__file__)
log_directory = Path(THIS_DIRECTORY, 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
file_name = f'game_logs{date.today().strftime("%m-%d")}.log'
new_log_path = Path(log_directory, file_name)
logger = logging.getLogger("regex_solver")
handler = logging.FileHandler(new_log_path)
format = logging.Formatter("%(asctime)s: %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


#=======================================================
#    Pydantic Models
#=======================================================
class GuessFeedback(BaseModel):
    guess: str
    feedback: str

class GameData(BaseModel):
    game_id: int
    token: str
    token_expiration: datetime = None
    solver_id: int
    solver_name: str
    status: bool = True
    guess_count: int
    
    """
    Guesses are nested dictionaries where the key represents the 
    guess number and the dictionary contains the guess and feedback for that guess number. 

    {   1: 
            {"guess": 'hello', "feedback": 'feedback'},
        2: 
            {"guess": 'hello', "feedback": 'feedback'},
        ...
    }
    """
    guesses: Optional[Dict[int, GuessFeedback]] = None
    correct_word: str
    message: str
    results: Optional[str] = None
    
    
class Guess(BaseModel):
    game_id: int
    token: str
    guess: str
    

#==========================================================================
#    Regex Solver Class
#==========================================================================
class RegexSolver:
    def __init__(self, username: str):
        self.username = username
        self.rounds: int = None
        self.user_id = USER_ID
        self.api_key = API_KEY

        # API 
        self.token: Optional[str] = None
        self.game_id: str = None
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
        except(requests.JSONDecodeError):
            logger.warning("Payload Error From Guess: %s", r.text)
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
        

    def _calculate_session_stats(self):
        logger.info("Wins: %i, Total Played %i", self.wins, self.total_played)
        self.average_wins = round(((self.wins / self.total_played) * 100), 2)
        self.average_guesses = round((self.total_guesses / self.wins), 2)
        logger.info("Average Wins: %2f, Average Guesses: %2f", self.average_wins, self.average_guesses)
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
        logger.info("Starting Regex-Solver session")      
        # Gameplay Loop
        while count <= self.rounds:
            logger.info("Round: %i", count)
            self._populate_words()
            self._reset_helpers()
            self._play_round()
            self.update_single_stats()
            count += 1
        self._calculate_session_stats()


#==========================================================================
# Main Program Loop
#==========================================================================
def main():
    solver_instance = RegexSolver(username='v8-dev')
    solver_instance.play(1000)

if __name__ == "__main__":
    main()
