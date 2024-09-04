import pytest
from app import db
from app.models import User, Solver, Game


@pytest.fixture(scope="module")
def api_lookups(test_client, init_database):

    user5 = User(
        username='user5',
        email='u5@gmail.com',
        confirmed=True
    )

    user5.set_password('test_password')
    db.session.add(user5)
    db.session.commit()

    solver51 = Solver(
        name='solver51',
        user_id =user5.id,
        api_id = '123456789qwertyuiopasdfghjklzxcvb',
        words_played=8,
        words_won=6,
        avg=75,
        avg_guesses=4,
        current_streak=0,
        max_streak=6
    )

    db.session.add(solver51)
    db.session.commit()


    game1 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='hutch',
        guess_count=4,
        guesses='tweed, joist, glean, hutch',
        feedback='YBBBB, BBBBY, BBBBB, GGGGG',
        results=True
    )

    db.session.add(game1)
    game2 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='ahead',
        guess_count=4,
        guesses='stage, moody, flock, ahead',
        feedback='BBYBY, BBBYB, BBBBB, GGGGG',
        results=True
    )

    db.session.add(game2)
    game3 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='twang',
        guess_count=4,
        guesses='grand, unzip, weedy, twang',
        feedback='YBGGB, BYBBB, YBBBB, GGGGG',
        results=True
    )

    db.session.add(game3)
    game4 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='smote',
        guess_count=4,
        guesses='embed, ovate, pouty, smote',
        feedback='YGBBB, YBBGG, BYBGB, GGGGG',
        results=True
    )

    db.session.add(game4)
    game5 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='sappy',
        guess_count=4,
        guesses='brick, horny, tangy, sappy',
        feedback='BBBBB, BBBBG, BGBBG, GGGGG',
        results=True
    )

    db.session.add(game5)
    game6 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='mirth',
        guess_count=4,
        guesses='hippo, whine, sonic, mirth',
        feedback='YGBBB, BYYBB, BBBYB, GGGGG',
        results=True
    )

    db.session.add(game6)
    db.session.commit()

    game7 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='heady',
        guess_count=6,
        guesses='heave, agree, plane, apron, kayak, taker',
        feedback='GGGBB, YBBYB, BBGBY, YBBBB, BYYBB, BYBYB',
        results=False
    )

    db.session.add(game7)
    game8 = Game(
        solver_id=solver51.id,
        user_id=user5.id,
        correct_word='alive',
        guess_count=6,
        guesses='epoxy, skate, shunt, snuck, badge, spite',
        feedback='YBBBB, BBYBG, BBBBB, BBBBB, BYBBG, BBGBG',
        results=False
    )

    db.session.add(game8)
    db.session.commit()

    yield


@pytest.fixture(scope="module")
def get_lookup_token(test_client, init_database):
    """Creates a token for tests inside of the test_api_lookups.py file that."""
    user = db.session.scalar(db.select(User).where(User.id == 5))
    token = user.get_api_token()
    return token