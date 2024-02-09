import pytest

from app import wordguess

def test_give_feedback_simple():
    correct_word = 'array'
    guess = 'ayaya'
    assert wordguess.give_feedback(correct_word, guess) == 'GYYBB'
    

test_give_feedback_simple()
