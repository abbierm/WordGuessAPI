"""
test_auth_routes.py tests the authentication blueprint routes to make sure they contain the correct content. 

This includes register, login, logout, and requesting a new password
"""

from app import db
from app.models import User, Game, Solver
from sqlalchemy import exc
import sqlalchemy as sa


def test_login_page(test_client):
    """
    GIVEN a flask app configured for testing
    WHEN '/auth/login' is requested (GET)
    THEN check is the response is valid
    """
    response = test_client.get('/auth/login')
    assert response.status_code == 200
    assert b'username' in response.data
    assert b'password' in response.data


def test_valid_login(test_client, init_database):
    """
    GIVEN a flask app configured for testing 
    WHEN '/auth/login' is requested (POST)
    THEN check if the response is valid
    """
    data = {
        'username': 'a_user',
        'password': 'testPassword1'
    }
    response = test_client.post('/auth/login', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logout' in response.data
    assert b'Log in' not in response.data
    

def test_invalid_login(test_client, init_database):
    """
    GIVEN a flask app configured for testing 
    WHEN '/auth/login' is requested (POST) with an invalid password
    THEN check is the correct error is flashed on the 'auth/login' page
    """
    data = {
        'username': 'a_user',
        'password': 'tdsgflksdfjlkf'
    }
    logout = test_client.get('/auth/logout')
    assert b'Log in' not in logout.data
    response = test_client.post('/auth/login', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data