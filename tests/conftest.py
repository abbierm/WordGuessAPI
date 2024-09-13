import pytest
from app import create_app, db, game_cache
from app.models import User, Solver, Game
from app.games import GameNode, create_payload
from config import Config



class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


@pytest.fixture(scope='function')
def new_user():
    user = User(username='a_cool_username', email='aTestEmail@email.com')
    return user


@pytest.fixture
def new_solver(new_user):
    solver = Solver(name='word_guess_solver', user_id=1, words_won=0, words_played=0)
    return solver


@pytest.fixture(scope="module")
def test_client():
    flask_app = create_app(TestConfig)
    client = flask_app.test_client()
    ctx = flask_app.test_request_context()
    ctx.push()

    yield client 

    ctx.pop()

    
@pytest.fixture(scope="module")
def init_database(test_client):
    db.create_all()

    user = User(
            username='user1', 
            email='u1@gmail.com', 
            confirmed=True
        )
    user.set_password('test_password')
    db.session.add(user)
    db.session.commit()

    user2 = User(
            username='user2', 
            email='u2@gmail.com', 
            confirmed=True
        )
    user2.set_password('test_password')
    db.session.add(user2)

    user3 = User(
            username='user3', 
            email='u3@gmail.com', 
            confirmed=True
        )
    user3.set_password('test_password')
    db.session.add(user3)

    user4 = User(
            username='user4', 
            email='u4@gmail.com', 
            confirmed=True
        )

    user4.set_password('test_password')
    db.session.add(user4)

    db.session.commit()

    solver11 = Solver(
            name='solver11',
            user_id=user.id
        )
    db.session.add(solver11)

    solver21 = Solver(
            name='solver21',
            user_id=user2.id,
            words_played=10,
            words_won=8,
            avg_guesses=4.5,
            avg=80,
            max_streak=5,
            current_streak=5,
            solver_id='bd64d06a6d271e3a9254afd0e7a94977'
        )
    db.session.add(solver21)

    solver22 = Solver(
            name='solver22',
            user_id=user2.id,
            words_played=100,
            words_won=50,
            avg_guesses=5,
            avg=50,
            max_streak=10,
            current_streak=0,
            solver_id='bd64d06a6d271e3a9254afd0e7a94978'
        )
    db.session.add(solver22)

    solver41 = Solver(
            name='solver41',
            user_id=user4.id,
            words_played=2,
            words_won=1,
            avg_guesses=5,
            avg=50,
            max_streak=1,
            current_streak=1,
            solver_id='bd64d06a6d271e3a9254afd0e7a94941'
        )
    db.session.add(solver41)
    solver42 = Solver(
            name='solver42', 
            user_id=4,
            words_played=100,
            words_won=90,
            avg=90,
            avg_guesses=5.1,
            max_streak=89,
            current_streak=0,
            solver_id='bd64d06a6d271e3a9254afd0e7a94942'
        )
    db.session.add(solver42)
    
    solver43 = Solver(
            name='solver43', 
            user_id=user4.id,
            words_played=100,
            words_won=90,
            avg=90,
            avg_guesses=5.1,
            max_streak=89,
            current_streak=0,
            solver_id='bd64d06a6d271e3a9254afd0e7a94943'
        )
    db.session.add(solver43)
    db.session.commit()

    game211 = Game(
            solver_id=solver21.id,
            user_id=user2.id,
            correct_word='tests',
            guess_count=4,
            guesses='aisle, files, texts, tests',
            feedback='BBGBY, BBBYG, GGBGG, GGGGG',
            results=True
        )
    db.session.add(game211)

    game411 = Game(
            solver_id=solver41.id,
            user_id=user4.id,
            correct_word='bleak',
            guess_count=6,
            guesses="tests, corgi, flask, ghost, these, bleep",
            feedback="BYBBB, BBBBB, BGYBG, BBBYY, YBYYB, GGGBB",
            results=False
        )
    
    db.session.add(game411)

    game412 = Game(
            solver_id=solver41.id,
            user_id=user4.id,
            correct_word='beats',
            guess_count=5,
            guesses="tests, corgi, flask, ghost, beats",
            feedback="BGBGG, BBBBB, BBGYB, BBBYY, GGGGG",
            results=True
        )
    db.session.add(game412)

    game431 = Game(
            solver_id=solver43.id,
            user_id=user4.id,
            correct_word='quite',
            guess_count=3,
            guesses="ghost, telex, quite",
            feedback="BBBBY, YYBBB, GGGGG",
            results=True
        )

    db.session.add(game431)
    db.session.commit()

    
    yield test_client

    db.drop_all()


#====================================================================
# Game Session For API gameplay
#+===================================================================
@pytest.fixture(scope="function")
def active_game(test_client, init_database):

    game432 = GameNode(
        game_token="9a1c3132784480a62ad8785cf77a6867",
        user_id=4,
        solver_name="solver43",
        solver_id=6,
        correct_word='buddy',
        guess_count=0,
        status=True
    )
    payload = create_payload(
                game=game432,
                include_feedback=False,
                include_correct=False
    )
    game_cache.put(game432)
    
    yield payload

    game_cache.remove("9a1c3132784480a62ad8785cf77a6867")


#====================================================================
# Authentication Class to pass to @login_required routes
#====================================================================

class AuthActions(object):
    def __init__(self, client):
        self._client = client
    
    def login(self):

        return self._client.post(
            '/auth/login',
            data={'username': 'user4', 'password': 'test_password'}, 
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(test_client, init_database):
    return AuthActions(test_client)


@pytest.fixture(scope="module")
def get_token(test_client, init_database):
    """Creates a token for user4 that can be used inside of start headers"""
    user4 = db.session.scalar(db.select(User).where(User.username == "user4"))
    token = user4.get_api_token()
    return token

