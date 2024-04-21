from collections import Counter
from datetime import datetime
import logging
import os
from pathlib import Path
from requests import get, post, JSONDecodeError
from words.correct import correct_words
import sys
from typing import Optional
#from decorators import add_logger


URL = 'http://127.0.0.1:5000/'


#===============================
#     logger
#===============================
THIS_DIRECTORY = os.path.dirname(__file__)
file_name = 'logs/' + 'game_logs.log'
logger = logging.getLogger('SliceAndBurnSolver')
log_path = Path(THIS_DIRECTORY, file_name)
handler = logging.FileHandler(log_path)
format = logging.Formatter("%(asctime)s: %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)




class SliceBurn:
    def __init__(self):
        self.username = 'v8-dev'
        self.solvername = 'sliceAndBurn'
        self.rounds: int = None
        self.current_round = 0
        self.words: Optional[set] = None
        self.guess_feedback: dict = {}
        self.current_payload: dict = None
        self.won: bool = False

        # Gameplay
        self.playing = True
        self.token = None
        self.game_id = None
        self.guesses = 0
        self.current_guess: str = None
        self.feedback: str = None

        # Next Guess Helpers
        self.word_so_far = [0, 1, 2, 3, 4]
        self.grey_letter_lst = []
        self.grey_letters = {0: '', 1: '', 2: '', 3: '', 4: ''}
        self.yellow_letter_lst = []
        self.yellow_letters = {0: [], 1: [], 2: [], 3: [], 4: []}
        self.counts: list[tuple] = None
        self.letter_scores = {}
        

        # Stats
        self.words_played = 0
        self.words_won = 0
        self.avg_won: float = None
        self.avg_guesses: float = None
        # Using guess_total because it is easier to calculate guess avg 
        self.guess_total = 0
    

        
#================================================
# API requests and parsing
#================================================        
    def _parse_start_payload(self, json: dict):
        """Gets game info and adds to instance variables"""
        self.game_id = json['game_id']
        self.token = json['token']
        self.current_payload = json       

    def _parse_guess_payload(self, json: dict):
        if self.token != json['token']:
            logger.debug('Incorrect Token received for round %i', self.current_round)
            sys.exit()
        self.current_payload = json
        self.guesses = int(json['guesses'])
        self.feedback = json["feedback"]
        self.playing = json["status"]
        logger.debug("Guess # %i, Received feedback: %s Current Guess: %s", self.guesses, self.feedback, self.current_guess)
        logger.debug("Current status: %s", self.playing)


    def _start_game(self):
        url = URL + f'/api/start/{self.username}/{self.solvername}'
        r = get(url)
        try:
            self._parse_start_payload(r.json())
            logger.debug("New Game ID %i", self.game_id)
        except JSONDecodeError as e:
            logger.debug("Starting game request error: %s", e)
            sys.exit()

    def _post_guess(self):
        payload = {
                    "game_id": self.game_id,
                    "token": self.token,
                    "guess": self.current_guess
                }
        url = URL + 'api/guess'
        r = post(url, json=payload)
        try:
            data = r.json()
            self._parse_guess_payload(data)
        except JSONDecodeError as e:
            logger.debug("Guess Request Error: %s", e)
            sys.exit()


#=========================================================================
# Solver Logic
#=========================================================================
    def _process_feedback(self):
        """Takes current feedback and proccess each of the letters and puts them in the correct helper spaces"""
        logger.debug("Feedback: %s", self.feedback)
        for i, color in enumerate(self.feedback):
            if color.upper() == 'G':
                self.word_so_far[i] = self.current_guess[i]
            elif color.upper() == 'Y':
                self.yellow_letters[i].append(self.current_guess[i])
            else:
                self.grey_letters[i] = self.current_guess[i]
                self.grey_letter_lst.append(self.current_guess[i])
        

    def _cull_words(self):
        """Uses helpers to remove words from list."""

        # Green Letters
        for i, letter in enumerate(self.words):
            new_words = [word for word in self.words if 
            word[i] == letter]
            logger.debug("Words after processing Green letters:\n%s", new_words)
            self.words = set(new_words)

        # Yellow Letters
        for index, lst in self.yellow_letters.items():
            for letter in lst:
                new_words = [word for word in self.words if letter not in word and word[index] != letter]
                logger.debug("Words after processing Yellow letters:\n%s", new_words)
                self.words = set(new_words)

        # Grey Letters
        for i, letter in self.grey_letters.items():
            if letter not in self.word_so_far and letter not in self.yellow_letter_lst:
                new_words = [word for word in self.words if letter in word]
                self.words = set(new_words)
        logger.debug("Words after processing Green letters:\n%s", new_words)
        logger.debug("%s", self.words)
            
    def _update_counts(self):
        counts = Counter()
        for word in self.words:
            for letter in word:
                counts.update(letter)
        self.counts = counts.most_common()
        logger.debug("%s", self.counts)
        
    def _update_letter_scores(self):
        """Gives each letter a score based on its frequency in the words that are left."""
        self.letter_scores = {}
        start_value = 26
        for tup in self.counts:
            self.letter_scores[tup[0]] = start_value
            start_value -= 1
        logger.debug("%s", self.letter_scores)
            

    def _pick_highest_score(self):
        """Gives each word a score and picks the word with the highest score."""
        word_scores = {}
        for word in self.words:
            word_score = 0
            for letter in word:
                word_score += self.letter_scores[letter]
            word_scores[word] = word_score
        logger.debug("%s", word_scores)
        self.current_guess = sorted(word_scores.items(), key=lambda item: item[1])[-1]
        

    def _pick_word(self):    
        # Seemed like a good first guess?
        if self.guesses == 0:
            self.current_guess = 'tears'
        else:
            self._process_feedback()
            self._cull_words()
            self._update_counts()
            self._update_letter_scores()
            self._pick_highest_score()

    
#=============================================
# Update Stats
#=============================================    
    def _process_results(self):
        self.words_played += 1
        if self.payload['results'] == 'won':
            self.won = True
            self.words_won += 1
            self.guess_total += self.guesses
            self.avg_guesses = round((self.guess_total / self.words_won), 2)
        else:
            self.won = False
        
        self.avg_won = round(((self.words_won / self.words_played) * 100), 2)
        

#=============================================
# Reset Gameplay Helpers
#=============================================
    
    

    def _reset_helpers(self):
        self.words = set(correct_words[:])
        self.word_so_far = [0, 1, 2, 3, 4]
        self.grey_letter_lst = []
        self.grey_letters = {0: '', 1: '', 2: '', 3: '', 4: ''}
        self.yellow_letter_lst = []
        self.yellow_letters = {0: [], 1: [], 2: [], 3: [], 4: []}
        self.playing = True
        self.guesses = 0
        self.current_guess = None
        self.feedback = None
        self.counts = None
        self.letter_scores = {}
        self.won = False
        self.current_payload = {}

# ===========================================================================
#   Gameplay - Loops
# ===========================================================================
    def _play_one_game(self):
        """Plays one game (trying to guess one 5 letter word in 5 guesses)"""
        self._start_game()
        while self.playing == True:
            self._pick_word()
            self._post_guess()
        self._process_results()
        logger.info("END OF ROUND: %i RESULTS", self.current_round)
        logger.info("Guess Feedback: %s", self.guess_feedback)
        logger.debug("Words played: %i, Words won: %i", self.words_played, self.words_won)
        logger.debug("Avg won: %f, Avg guesses: %f", self.avg_won, self.avg_guesses)

    
    def play(self, rounds: int = 250):
        logger.debug("Starting new WordGuess session")
        self.rounds = rounds     
        while self.current_round <= rounds:
            self._reset_helpers()
            self.current_round += 1
            logger.debug("Starting round %i of %i", \
                        self.current_round, self.rounds)
            self._play_one_game()
        
        logger.info("Words: %i, Won: %i, Avg wins: %f, Avg guesses: %f")
            
            


    

def main():
    new_slice_instance = SliceBurn()
    new_slice_instance.play(5)



if __name__ == '__main__':
    main()


