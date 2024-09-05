import pytest
from app.games import GameNode
from datetime import datetime, timezone, timedelta


@pytest.fixture(scope="function")
def new_game():
    game = GameNode(
        game_token = "test_token_abc123",
        token_expiration=datetime.now(timezone.utc) + 
                timedelta(seconds=36000),
        solver_name="unit_test_solver",
        solver_id=123,
        user_id=123,
        correct_word="hello",
        guess_count=1,
        guesses=["tests"],
        feedback=["BGBBB"]
    )

    yield game


