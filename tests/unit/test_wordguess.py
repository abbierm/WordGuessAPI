from app import wordguess

# Testing gameplay loop from app/wordguess.py

def test_choose_word():
    """
    Check _choose_word() function returns a valid wordle word.
    """
    word = wordguess._choose_word()
    assert len(word) == 5
    assert isinstance(word, str)


def test_validate_guess():
    """
    Given a word
    Check if the word is in dictionary
    """
    word1 = 'aisle'
    word2 = 'ghfse'
    word3 = 'breaks'
    assert wordguess._validate_guess(word1) == True
    assert wordguess._validate_guess(word2) == False
    assert wordguess._validate_guess(word3) == False


def test_feedback():
    """
    Given a correct word and a guess
    Check if the feedback is correct and in the correct format
    """
    # Weird 3 of the same letter guess
    correct_word1 = 'affix'
    guess1 = 'faffy'
    assert wordguess._feedback(correct_word1, guess1) == 'YYGBB'

    # Simple feedback
    correct_word2 = 'ghost'
    guess2 = 'great'
    assert wordguess._feedback(correct_word2, guess2) == 'GBBBG'

    # The correct word
    correct_word3 = 'right'
    guess3 = 'right'
    assert wordguess._feedback(correct_word3, guess3) == 'GGGGG'

