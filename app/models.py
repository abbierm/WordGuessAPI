from app import db, login
from datetime import datetime, timezone, timedelta
from time import time
import secrets
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    confirmed: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    solvers: so.WriteOnlyMapped['Solver'] = so.relationship(
                                            back_populates='user')
    
    games: so.WriteOnlyMapped['Game'] = so.relationship(
                                            back_populates='user')
    

    #===========================================================================
    # API user lookup
    #===========================================================================
    
    def to_dict(self):
        payload = {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }
        return payload
    
    #===========================================================================
    # Password setting / hashing / resetting 
    #===========================================================================

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password) ->bool:
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(User, id)
    
    #===========================================================================
    # Account Confirmation Token
    #===========================================================================

    def generate_confirmation_token(self, expires_in=600):
        return jwt.encode(
            {'confirm_email': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verift_account(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['confirm_email']
        except Exception:
            return
        return db.session.get(User, id)


    #===========================================================================
    # Registration safeguards to prevent duplicates username/emails
    #===========================================================================

    @staticmethod
    def check_duplicate_username(new_username: str) -> bool:
        """Returns true if there is already an account associated with new_username"""
        user = db.session.scalar(db.select(User).where(User.username == new_username))
        if user:
            return True
        return False
              
    @staticmethod
    def check_duplicate_email(new_email: str) -> bool:
        """Returns True is there is already an account associated with new_email."""
        user = db.session.scalar(db.select(User).where(User.email == new_email))
        if user:
            return True
        return False

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))



class Solver(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    user_id: so.Mapped[int] = so.mapped_column(
                                            sa.ForeignKey(User.id), index=True)
    user: so.Mapped[User] = so.relationship(back_populates='solvers')
    words_played: so.Mapped[int] = so.mapped_column(default=0)
    words_won: so.Mapped[int] = so.mapped_column(default=0)
    games: so.WriteOnlyMapped['Game'] = so.relationship(back_populates='solver')

    def to_dict(self):
        payload = {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "words_played": self.words_played,
            "words_won": self.words_won,
        }
        return payload

    def update_stats(self, won: bool):
        self.words_played += 1
        if won == True:
            self.words_won += 1
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def validate_user_solver(username, solver_name) -> bool:
        user = db.session.scalar(sa.select(User).where(
                                        User.username == username))
        solver = db.session.scalar(sa.select(Solver).where(
                                        Solver.name == solver_name))
        if user.id != solver.user_id:
            return False
        return True


class Game(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
                                        sa.ForeignKey(User.id),index=True)
    solver_id: so.Mapped[int] = so.mapped_column(
                                        sa.ForeignKey(Solver.id),index=True)
    token: so.Mapped[Optional[str]] = so.mapped_column(
                                        sa.String(32),index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]
    user: so.Mapped[User] = so.relationship(back_populates='games')
    solver: so.Mapped[Solver] = so.relationship(back_populates='games')
    correct_word: so.Mapped[str] = so.mapped_column(sa.String(10))
    guesses: so.Mapped[int] = so.mapped_column(default=0)
    current_guess: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10))
    current_feedback: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10))
    # True is active, false is inactive
    status: so.Mapped[bool] = so.mapped_column(default=True)
    # True is won, False is Lost
    results: so.Mapped[Optional[bool]] = so.mapped_column(default=None)

    def get_token(self, expires_in=36000):
        """
        Referenced Miguel Grinberg's Flask Mega-Tutorial 
        to help create this get_token and check_token functions. 
        """

        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(
                tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def check_token(token):
        user_game = db.session.scalar(sa.select(Game).where(Game.token == token))
        if user_game is None:
            return False
        if user_game.token_expiration.replace(
                            tzinfo=timezone.utc) < datetime.now(timezone.utc):
            print('expired game token')
            return False
        return True
    
    def update_game(self, guess, feedback):
        """ Updates the database."""
        self.guesses += 1
        self.current_guess = guess
        self.current_feedback = feedback
        if feedback == "GGGGG":
            self.status = False
            self.results = True
        elif self.guesses == 6:
            self.status = False
            self.results = False
        db.session.add(self)
        db.session.commit()
                
    def create_payload(self, include_correct=False, include_feedback=False, message=None):
        payload = {
            'game_id': self.id,
            'token': self.token,
            'token_expiration': self.token_expiration.isoformat(),
            'user_id': self.user_id,
            'solver_id': self.solver_id,
            'solver_name': self.solver.name,
            'status': self.status,
            'guesses': self.guesses,
            'guess': 'None',
            'feedback': 'N/A',
            'correct_word': '*****',
            'message': 'None',
            'results': 'None'
        }
        if include_feedback == True:
            payload["guess"] = self.current_guess
            payload["feedback"] = self.current_feedback
        if include_correct == True:
            payload["correct_word"] = self.correct_word
            if self.results == True:
                payload["results"] = 'won'
            else:
                payload["results"] = 'lost'
        if message != None:
            payload["message"] = message
        return payload
