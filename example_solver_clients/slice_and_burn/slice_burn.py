# slice_burn.py is an example WordGuess solver that
# uses a culling and letters-remained strategy to 
# pick the next word

from collections import Counter
from datetime import date
import logging
import os
from pathlib import Path
import requests
from requests import post, JSONDecodeError
from requests.auth import HTTPBasicAuth
from words.correct import correct_words
import sys
from typing import Optional
import keyring


URL = 'http://127.0.0.1:5000/'



# =========================================================================
# Logging
# =========================================================================
THIS_DIRECTORY = os.path.dirname(__file__)
log_directory = Path(THIS_DIRECTORY, 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
file_name = f'game_logs_{date.today().strftime("%m-%d")}.log'
logger = logging.getLogger('SliceAndBurnSolver')
log_path = Path(log_directory, file_name)
handler = logging.FileHandler(log_path)
format = logging.Formatter("%(asctime)s: %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


# =========================================================================
#     Slice and Burn Solver Class
# =========================================================================
class SliceBurn:
    def __init__(self):
        self.username = 'devUser'
        self.app_password = keyring.get_password(
            "wordguess_password", 
            "devUser"
        )
        self.solver_id = keyring.get_password(
            "api_id",
            "slice"
        )
        self.token: str = None
        self.header = {
            "Authorization": None
        }
        self.rounds: int = None
        self.current_round = 0
        self.words: Optional[set] = None
        self.guesses: dict = {}
        self.results: Optional[str] = None

        # Gameplay
        self.playing = True
        self.game_token = None
        self.guess_count = 0
        self.current_guess: str = None
        self.feedback: str = None

        # Helpers
        self.green_letters = [0, 1, 2, 3, 4]
        self.constructed_word = [0, 1, 2, 3, 4]
        self.grey_letters = [0, 1, 2, 3, 4]
        self.grey_letter_set = set()
        self.yellow_letters = [0, 1, 2, 3, 4]
        self.yellow_letter_set = set()
        self.counts: list[tuple] = None
        self.letter_scores = {}
        
        # Stats
        self.words_played = 0
        self.words_won = 0
        self.avg_won: float = None
        self.avg_guesses: float = None 
        self.guess_total = 0
    

# =========================================================================
# API requests and parsing
# =========================================================================    

    def _unload_response(self, payload: dict):
        
        self.guess_count = payload["guess_count"]
        if self.guess_count == 0:
            self.game_token = payload["game_token"]
        else:
            self.feedback = payload["guesses"][str(self.guess_count)]["feedback"]
            self.guesses = guesses = payload["guesses"]
        self.playing = payload["status"]

        logger.info("Guess # %i, Current Guess: %s, Current Feedback: %s, status %s", self.guess_count, self.current_guess, self.feedback, self.playing)
        
        if self.playing == False:
            self.results = payload["results"]
            if self.results == 'lost':
                logger.info("Correct Word: %s", payload["correct_word"])


    def _request_token(self):
        url = URL + 'api/tokens'
        basic_auth = HTTPBasicAuth(
            self.username,
            self.app_password
        )
        try:
            token_request = requests.post(
                url = url,
                auth=basic_auth
            )
            self.token = token_request.json()["token"]
            self.header["Authorization"] = f"Bearer {self.token}"
        except (JSONDecodeError, KeyError) as e:
            logger.debug("Token Request Error: %s", e)
            sys.exit()


    def _start_game(self):
        url = URL + '/api/start'
        payload = {"solver_id": self.solver_id}
        r = post(url=url, json=payload, headers=self.header)
        try:
            self._unload_response(r.json())
        except JSONDecodeError as e:
            logger.warning("Starting game request error: %s", e)
            sys.exit()


    def _post_guess(self):
        payload = {
                    "game_token": self.game_token,
                    "guess": self.current_guess
        }
        url = URL + 'api/guess'
        r = post(url, json=payload, headers=self.header)
        try:
            data = r.json()
            self._unload_response(data)
        except (JSONDecodeError, KeyError ) as e:
            logger.debug("Guess Request Error: %s", e)
            sys.exit()


# =========================================================================
# Logic that picks next word
# =========================================================================
    def _process_feedback(self):
        """Uses feedback and current guess to create helpers that cull words."""
        self.grey_letters = [0, 1, 2, 3, 4]
        self.yellow_letters = [0, 1, 2, 3, 4]
        self.green_letters = [0, 1, 2, 3, 4]
        for i, color in enumerate(self.feedback):
            if color.upper() == 'G':
                self.green_letters[i] = self.current_guess[i]
                self.constructed_word[i] = self.current_guess[i]
            elif color.upper() == 'Y':
                self.yellow_letters[i] = self.current_guess[i]
                self.yellow_letter_set.add(self.current_guess[i])
            else:
                self.grey_letters[i] = self.current_guess[i]
                self.grey_letter_set.add(self.current_guess[i])
        

    def _cull_words(self):
        """Uses helpers to remove words from the list."""
        
        # Green Letters- culls words without matching green letters
        for index, letter in enumerate(self.green_letters):
            if isinstance(letter, str):
                new_words = [word for word in self.words if word[index] == letter]
                self.words = set(new_words)
        
        # Yellow Letters - Culls the word if the word doesn't have that letter
        for index, letter in enumerate(self.yellow_letters):
            if isinstance(letter, str):
                new_words = [word for word in self.words if word[index] != letter and letter in word]
                self.words = set(new_words)
                
        # Grey Letters
        for index, letter in enumerate(self.grey_letters):
            if isinstance(letter, str):
                new_words = [word for word in self.words if word[index] != letter]
                self.words = set(new_words)
            
                if letter not in self.constructed_word and letter not in self.yellow_letter_set:
                    new_words = [word for word in self.words if letter not in word]
                    self.words = set(new_words)
            

    def _update_counts(self):
        counts = Counter()
        for word in self.words:
            for letter in word:
                counts.update(letter)
        self.counts = counts.most_common()
        
    def _update_letter_scores(self):
        """Gives each letter a score based on its frequency in the words that are left."""
        self.letter_scores = {}
        start_value = 26
        for tup in self.counts:
            self.letter_scores[tup[0]] = start_value
            start_value -= 1
        
            
    def _pick_highest_score(self):
        """Gives each word a score and picks the word with the highest score."""
        word_scores = {}
        for word in self.words:
            word_score = 0
            for letter in word:
                word_score += self.letter_scores[letter]
            word_scores[word] = word_score
        
        self.current_guess = sorted(word_scores.items(), key=lambda item: item[1])[-1][0]
        

    def _pick_word(self):    
        if self.guess_count == 0:
            self.current_guess = 'tears'
        else:
            self._process_feedback()
            self._cull_words()
            self._update_counts()
            self._update_letter_scores()
            self._pick_highest_score()

    
# =========================================================================
# Update Stats
# =========================================================================
    def _process_results(self):
        self.words_played += 1
        if self.results == 'won':
            self.words_won += 1
            self.guess_total += self.guess_count
            self.avg_guesses = round((self.guess_total / self.words_won), 2)
        self.avg_won = round(((self.words_won / self.words_played) * 100), 2)
        logger.debug("Round %i results %s, Words Won: %i, Avg Guesses: %f, Avg Wins: %f", self.current_round, self.results, self.words_won, self.avg_guesses, self.avg_won)
        
        

# =========================================================================
# Reset Gameplay Helpers
#==========================================================================
    def _reset_helpers(self):
        self.words = set(correct_words[:])
        self.green_letters = [0, 1, 2, 3, 4]
        self.constructed_word = [0, 1, 2, 3, 4]
        self.grey_letters = [0, 1, 2, 3, 4]
        self.grey_letter_set = set()
        self.yellow_letters = [0, 1, 2, 3, 4]
        self.yellow_letter_set = set()
        self.playing = True
        self.guess_count = 0
        self.current_guess = None
        self.feedback = None
        self.counts = None
        self.letter_scores = {}
        self.won = False
        self.current_payload = {}


# =========================================================================
#   Gameplay - Loops
# =========================================================================
    def _play_one_game(self):
        """Plays one game (trying to guess one 5 letter word in 5 guesses)"""
        
        self._start_game()
        while self.playing == True:
            self._pick_word()
            self._post_guess()
        self._process_results()
        
        
    def play(self, rounds: int = 250):
        logger.info("Starting new WordGuess session")
        self._request_token()
        self.rounds = rounds     
        while self.current_round < rounds:
            self._reset_helpers()
            self.current_round += 1
            logger.info("Starting round %i of %i", self.current_round, self.rounds)
            self._play_one_game()


# =========================================================================
# Main Program
# =========================================================================
def main():
    new_slice_instance = SliceBurn()
    new_slice_instance.play(1000)

if __name__ == '__main__':
    main()


