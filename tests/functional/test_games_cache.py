"""
Tests the in-memory GameCache that stores games while they are still being 
played by the user. 
"""

import pytest
from app import game_cache
from app.games import GameNode


def test_add_game(init_cache, new_game_node):
    """
    GIVEN an active application and a new game instance,
    WHEN the new game is added to the game_cache,
    THEN check if game can be retrieved with the get() method
    """
    game_cache.put(new_game_node)
    game = game_cache.get("123abc")
    assert game is not None
    assert game.game_token == new_game_node.game_token


def test_cache_limit(init_cache, new_game_node):
    """
    GIVEN an active application and a new_game_node instance,
    WHEN 50 active games are added to the game_cache after adding 
        new_game_node
    THEN check if the new_game_node was removed.
    """
    game_cache.put(new_game_node)
    for i in range(50):
        new = GameNode(
            game_token=f"{i}test_token",
            solver_name="test_solver",
            solver_id=1,
            user_id=1,
            correct_word="tests",
        )
        game_cache.put(new)
    assert game_cache.get("123abc") is None


def test_game_cache_remove_method(init_cache, new_game_node):
    """
    GIVEN an active application and a new_game_node instance,
    WHEN new_game_node is added to the cache with the put method
        and then removed,
    THEN check if the new_game_node can be retrieved with the get method.
    """
    game_cache.put(new_game_node)
    game_cache.remove("123abc")
    x = game_cache.get("123abc")
    assert x is None


def test_game_cache_lru(init_cache, new_game_node):
    """
    GIVEN an active application and a new_game_node,
    WHEN new_game_node is added to the cache, followed by adding 25 games, 
        then new_game_node will be retrieved, and then 25 more games will 
        be added to the cache.
    THEN check is new_game_node is still in the cache with the get() method
    """
    game_cache.put(new_game_node)
    for i in range(25):
        new = GameNode(
            game_token=f"{i}test_token",
            solver_name="test_solver",
            solver_id=1,
            user_id=1,
            correct_word="tests",
        )
        game_cache.put(new)
    assert game_cache.get("123abc") is not None

    for j in range(25, 51):
        new2 = GameNode(
            game_token=f"{j}test_token",
            solver_name="test_solver",
            solver_id=1,
            user_id=1,
            correct_word="tests",
        )
        game_cache.put(new2)

    assert game_cache.get("123abc") is not None
    assert game_cache.get("0test_token") is None