import datetime
import logging
import os
from pathlib import Path
from pydantic import BaseModel
import random
import re
import requests
import sys
import time
from typing import Optional, List
from words.correct import correct_words


#==========================================================================
#    Logging
#==========================================================================
THIS_DIRECTORY = os.path.dirname(__file__)
logging_file = str(Path(THIS_DIRECTORY, 'logs', 'game_log.log'))

logger = logging.getLogger("regex_solver")
handler = logging.FileHandler(logging_file)
format = logging.Formatter("%(asctime)s: %(message)s")

handler.setFormatter(format)
logger.addHandler(handler)

logger.setLevel(logging.INFO)


#==========================================================================
#    Pydantic Models
#==========================================================================

class Feedback(BaseModel):
    guess_number: int
    guess: str
    feedback: Optional[str] = None


class GameData(BaseModel):
    game_id: str
    username: str
    total_guesses: int
    offical_guesses: int
    correct_word: Optional[str] = None
    status: bool = True
    result: Optional[str] = None
    guesses: Optional[List[Feedback]]

#==========================================================================
#    Regex Solver Class
#==========================================================================

class RegexSolver:
    def __init__(self, username: str):
        self.username = username
        self.rounds: int = None

        # API 
        self.payload: GameData = None
        self.current_feedback: Feedback = None
        self.game_id: str = None
        self.status: bool = True

        # Helpers to pick next word
        self.words = None
        self.offical_guesses = 0
        self.payload: GameData = None
        self.current_feedback: Feedback = None
        self.all_yellow = []
        self.grey_letters = [0, 1, 2, 3, 4]
        self.constructed_word = [0, 1, 2, 3, 4]
        self.yellow_letters = [0, 1, 2, 3, 4]
        self.regex_pattern_list = [0, 1, 2, 3, 4]
        self.regex_pattern = None
        
        # Stores total game data
        self.total_played = 0
        self.wins: int = 0
        self.losses: int = 0
        self.average_wins: float = None
        self.average_guesses: float = None


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
        self.payload = None
        self.current_feedback = None
        self.regex_pattern = ''
        self.offical_guesses = 0
        self.total_guesses = 0
        

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
        for i, feedback in enumerate(self.current_feedback.feedback):
            letter = self.current_feedback.guess[i]
            if feedback == "G":
                self.constructed_word[i] = letter
            elif feedback == 'Y':
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
        logger.debug("New Pattern: %s from feedback: %s", self.regex_pattern, self.current_feedback.feedback)
        

    def _filter_words(self):
        filtered_list = list(filter(lambda v: re.match(self.regex_pattern, v), self.words))
        self.words = filtered_list
        
          
    def _pick_best_first_word(self) -> str:
        # "Good" first wordle word choices
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


    def pick_next_word(self) -> str:
        if self.offical_guesses == 0:
            return self._pick_best_first_word()
        self._make_regex_pattern()
        self._filter_words()
        if len(self.words) == 0:
            return "loser"
        choice = self._choose()
        return choice
        
    
#==========================================================================
#    api 
#==========================================================================
    def _unload_payload(self):
        """
        Updates guess counts, current feedback and reports current status to the game-loop for flow control. 
        """
        self.offical_guesses = self.payload.offical_guesses
        self.total_guesses = self.payload.total_guesses
        self.current_feedback = self.payload.guesses[-1]
        self.status = self.payload.status
        logger.debug("for guess %s received feedback: [%s]", self.current_feedback.guess, self.current_feedback.feedback)
        
    
    def start(self, url=None):
        if url is None:
            url = f'http://127.0.0.1:5000/api/start/{self.username}'
        r = requests.get(url)
        try:
            x = r.json()
            self.game_id = x["game_id"]
        except (requests.JSONDecodeError):
            # TODO: Log Something
            print(f"{r.text()}")
            sys.exit()
    

    def guess(self, guess: str):
        url = 'http://127.0.0.1:5000/api/guess'
        payload = {"game_id": self.game_id, "guess": guess}
        r = requests.post(url, json=payload)
        try:
            x = r.json()
            self.payload = GameData(**x)
        except(requests.JSONDecodeError):
            print(f"{r.text}")
            sys.exit()


#==========================================================================
#    Updates Stats
#==========================================================================
    def _record_loss(self, file_name):
        with open(file_name, 'a') as f:
            f.write(f"Round: {self.total_played} Correct Word: {self.payload.correct_word}\n", )
            for i in self.payload.guesses:
                f.write(f"Guess Number: {i.guess_number} Guess: {i.guess}    Feedback: {i.feedback}\n")
            f.write("\n\n")
            
        
    def _calculate_win_average(self):
        self.average_wins = round(((self.wins / self.total_played) * 100), 2)


    def _calculate_average_guesses(self):
        if self.wins == 1:
            self.average_guesses = self.payload.offical_guesses
        else:
            old_guess_sum = self.average_guesses * (self.wins - 1)
            new_guess_sum = old_guess_sum + self.payload.offical_guesses
            self.average_guesses = round((new_guess_sum / self.wins), 2)
        

    def update_stats(self):
        self.total_played += 1
        if self.payload.result == 'won':
            self.wins += 1
            self._calculate_average_guesses()
        else:
            self.losses += 1
        self._calculate_win_average()
        logger.info("Games Played: %d, Wins: %d, losses: %d", self.total_played, self.wins, self.losses)
        logger.info("Valid Guesses: %d, Total Guesses: %d", self.offical_guesses, self.total_guesses)
        logger.info("Updated Win Average: %d, Updated Guess Average: %d", self.average_wins, self.average_guesses)


#==========================================================================
#    Gameplay loop
#==========================================================================
        
    def _play_round(self):
        self.start()
        while self.offical_guesses < 6:
            new_guess = self.pick_next_word()
            self._reset_lists()
            self.guess(new_guess)
            self._unload_payload()
            if self.status == False:
                return


    def play(self, rounds: int):
        self.rounds = rounds

        #Logging and Documenting losses
        logger.info("Starting Regex-Solver session")
        now = datetime.datetime.now().strftime("lost_log_%m-%d-%y_%H:%M.txt")
        new_file = Path(THIS_DIRECTORY, 'logs', now)

        # Gameplay
        while self.rounds > 0:
            logger.info("Starting next round")
            self._populate_words()
            self._reset_helpers()
            self._play_round()
            self.update_stats()

            logger.info("Results: \n %s", self.payload.model_dump(exclude="username"))
            if self.payload.result == 'lost':
                self._record_loss(new_file)

            self.rounds -= 1


        logger.info("END OF GAME RESULTS")
        logger.info("TOTAL WINS: %d, TOTAL LOSSES: %d, AVERAGE WINS: %d, AVERAGE GUESSES: %d", self.wins, self.losses, self.average_wins, self.average_guesses)
        

#==========================================================================
# Main Program - Runs when user imputs 'python regex_solver.py' in the terminal
#==========================================================================

def main():
    solver_instance = RegexSolver(username='hiro')
    solver_instance.play(20)



if __name__ == "__main__":
    main()

