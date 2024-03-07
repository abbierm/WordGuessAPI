from app import db
from datetime import datetime, timezone, timedelta
from flask import current_app, url_for
import secrets
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy.orm as so
from typing import Optional



class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    solvers: so.WriteOnlyMapped['Solver'] = so.relationship(
                                            back_populates='user')
    games: so.WriteOnlyMapped['Game'] = so.relationship(
                                            back_populates='user')


    @staticmethod
    def validate_user(username) -> bool:
        try:
            the_user = db.session.scalars(db.select(User).filter_by
            (username=username))
            return True
        except SqlalchemyError as e:
            """
            # TODO   
            Need to determine what the specific error would be if the user doesn't exist so we can create a new user. 
            """
            print(e)
            return False



class Solver(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                index=True)
    user: so.Mapped[User] = so.relationship(back_populates='solvers')
    words_played: so.Mapped[int] = so.mapped_column(default=0)
    words_won: so.Mapped[int] = so.mapped_column(default=0)

    games: so.WriteOnlyMapped['Game'] = so.relationship(
                                            back_populates='solver')

    @staticmethod
    def validate_solver(solver_name) -> bool:
        solver = db.session.scalars(db.select(Solver).filter_by
                                        (solver_name=solver_name))


    @staticmethod
    def validate_user_solver(username, solver_name) -> bool:
        user = db.session.scalars(db.select(User).filter_by(username=username))
        solver = db.session.scalars(db.select(Solver).filter_by
                                        (solver_name=name))
        if user.id != solver.id:
            return False
        return True



class Game(db.Model):
    # Game-ID
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    
    # Game Token
    token: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(32),index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]

    # Foreign Keys
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                index=True)
    solver_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Solver.id),
                                                index=True)

    user: so.Mapped[User] = so.relationship(back_populates='games')
    solver: so.Mapped[Solver] = so.relationship(back_populates='games')
    correct_word: so.Mapped[str] = so.mapped_column(sa.String(10))
    offical_guesses: so.Mapped[int] = so.mapped_column(default=0)

    # Only storing offical guesses
    guess_1: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5), 
                                                    default=None)
    feedback_1: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5),
                                                    default=None)

    guess_2: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5),
                                                    default=None)
    feedback_2: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5),
                                                    default=None)

    guess_3: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5), default=None)
    feedback_3: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5), 
                                                    default=None)

    guess_4: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5),
                                                    default=None)
    feedback_4: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5), 
                                                    default=None)

    guess_5: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5), 
                                                    default=None)
    feedback_5: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5),
                                                    default=None)

    guess_6: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5), default=None)
    feedback_6: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5),
                                                    default=None)
               
    status: so.Mapped[bool] = so.mapped_column(default=True)
    # True = won, False = lost
    results: so.Mapped[Optional[bool]] = so.mapped_column(default=None)


    """
    User pulls up the current games via api tokens rather than id or their username.  If the game is expired then the token won't work and a new game will be created. 

    """
    def get_token(self, expires_in=36000):
        # Used Miguel's mega flask tutorial to help create the token functions
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(
                tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = datetime.now(timezone.utc) - timedelta(
            seconds=1)

    @staticmethod
    def check_token(token):
        user_game = db.session.scalar(sa.select(Game).where(Game.token == token))
        if user_game is not None or user_game.token_expiration.replace(
                    tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return False
        return True

    
    def update_game(self, guess, feedback):
        self.offical_guesses += 1
        x = self.offical_guesses
        # TODO: Somehow make this 'dynamic' naming better
        guess_dict = {
            1: self.guess_1,
            2: self.guess_2,
            3: self.guess_3,
            4: self.guess_4,
            5: self.guess_5,
            6: self.guess_6,
        }
        feedback_dict = {
            1: self.feedback_1,
            2: self.feedback_2,
            3: self.feedback_3,
            4: self.feedback_4,
            5: self.feedback_5,
            6: self.feedback_6
        }

        self_guess = guess_dict[x]
        self_feedback = feedback_dict[x]
        self_guess, self_feedback = guess, feedback
        if feedback == "GGGGG":
            self.status = False
            self.results = True
        elif self.offical_guesses == 6:
            self.status = False
            self.results = False
        db.session.commit()


    def create_payload(self, include_correct=False, message=None):
        payload = {
            'game_id': self.id,
            'token': self.token,
            'token_expiration': self.token_expiration,
            'user_id': self.user_id,
            'status': self.status,
        }
        for i in range(6):
            current_guess = f"guess_{i + 1}"
            if self.current_guess != None:
                payload[current_guess] = self.current_guess
            else:
                break
        if include_correct == True:
            payload["correct_word"] = self.correct_word
        if message != None:
            paylaod["message"] = message
        return payload

    