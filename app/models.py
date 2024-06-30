from app import db, login
from datetime import datetime, timezone, timedelta
from time import time
import secrets
import sqlalchemy as sa
from sqlalchemy import and_
import sqlalchemy.orm as so
from typing import Optional, List
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
    solvers: so.Mapped[List['Solver']] = so.relationship(
                                        lazy="joined", cascade='all, delete-orphan', passive_deletes=True)
   
    #===========================================================================
    # API user lookup
    #===========================================================================
    
    def to_dict(self):
        payload = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "solvers": [solver.name for solver in self.solvers]
        }
        return payload
    
    #===========================================================================
    # Password setting / hashing / resetting 
    #===========================================================================

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        # db.session.add(self)
        # db.session.commit()

    def check_password(self, password) -> bool:
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
    def verify_account(token):
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
                                    sa.ForeignKey(User.id, ondelete="cascade"))
    words_played: so.Mapped[int] = so.mapped_column(default=0)
    words_won: so.Mapped[int] = so.mapped_column(default=0)
    avg: so.Mapped[float] = so.mapped_column(default=0)
    avg_guesses: so.Mapped[float] = so.mapped_column(
                                        default=None, nullable=True)
    current_streak: so.Mapped[int] = so.mapped_column(default=0)
    max_streak: so.Mapped[int] = so.mapped_column(default=0)
    games: so.WriteOnlyMapped['Game'] = so.relationship(back_populates='solver',
                            cascade='all, delete-orphan', passive_deletes=True)
    api_key: so.Mapped[Optional[str]] = so.mapped_column(
                                    sa.String(32), index=True, unique=True, nullable=True, default=None)
    

    #===========================================================================
    # API 
    #===========================================================================
    def to_dict(self):
        payload = {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "words_played": self.words_played,
            "words_won": self.words_won,
            "avg_guesses": self.avg_guesses,
            "avg_won": self.avg,
            "max_streak": self.max_streak,
            "api_key": self.api_key
        }
        return payload
    
    def make_api_key(self) -> str:
        self.api_key = secrets.token_hex(16)
        db.session.add(self)
        db.session.commit()
        return
    
    @staticmethod
    def check_key(key):
        solver = db.session.scalar(sa.select(Solver).where(Solver.api_key == key))
        return solver
    
    @staticmethod
    def get_solver(api_key: str):
        """Returns solver instance or None"""
        return db.session.scalar(sa.select(Solver).where(Solver.api_key == api_key))
    
    @staticmethod
    def validate_user_solver(username, solver_name) -> bool:
        user = db.session.scalar(sa.select(User).where(
                                        User.username == username))
        solver = db.session.scalar(sa.select(Solver).where(
                                        Solver.name == solver_name))
                                        
        if solver is None or user is None:
            return False
        elif user.id != solver.user_id:
            return False
        else:
            return True
        

    #===========================================================================
    # Solver Gameplay Stat Functions 
    #===========================================================================
   
    def calculate_avg_guesses(self, guess_count: int) -> float:
        """Calculates the avg number of guesses only in winning games."""
        if self.avg_guesses == None:
            return float(guess_count)
        guess_sum = self.avg_guesses * (self.words_won - 1)
        new_guess_avg = round(((guess_sum + guess_count) / self.words_won), 2)
        return new_guess_avg
        
    def update_stats(self, won: bool, guess_count: int):
        """Updates stats after a game. Not used for a clean refresh."""
        self.words_played += 1
        if won == True:
            self.words_won += 1
            self.current_streak += 1
            if self.current_streak > self.max_streak:
                self.max_streak = self.current_streak
        else:
            self.current_streak = 0
        self.avg = round(((self.words_won / self.words_played) * 100), 2)
        if won == True:
            self.avg_guesses = self.calculate_avg_guesses(guess_count)
        db.session.add(self)
        db.session.commit()

    def reset_games(self):
        """Deletes all of the games for this solver and updates their stats"""
        db.session.execute(sa.delete(Game).where(Game.solver_id == self.id))
        self.words_played = 0
        self.avg = 0
        self.words_won = 0
        self.avg_guesses = None
        self.current_streak = 0
        self.max_streak = 0
        db.session.add(self)
        db.session.commit()


    def get_games(self, filter=None):
        """Returns a game query not executed"""
        if filter is None or filter != "lost" and filter != "won":
           return sa.select(Game).where(Game.solver_id == self.id)
        elif filter == "lost":
           return sa.select(Game).where(and_(Game.solver_id == self.id, Game.results == False))
        elif filter == "won":
           return sa.select(Game).where(and_(Game.solver_id == self.id, Game.results == True))


class Game(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    solver_id: so.Mapped[int] = so.mapped_column(
                                        sa.ForeignKey(Solver.id),index=True)
    token: so.Mapped[Optional[str]] = so.mapped_column(
                                        sa.String(32),index=True, unique=True, default=None)
    token_expiration: so.Mapped[Optional[datetime]]
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, 
                                    default=lambda: datetime.now(timezone.utc))
    solver: so.Mapped[Solver] = so.relationship(back_populates='games')
    correct_word: so.Mapped[str] = so.mapped_column(sa.String(10))
    guess_count: so.Mapped[int] = so.mapped_column(default=0)
    guesses: so.Mapped[Optional[str]] = so.mapped_column(sa.String(40), default='')
    feedback: so.Mapped[Optional[str]] = so.mapped_column(sa.String(40), default='')
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
            return False
        return True
    
    def update_game(self, guess, feedback):
        self.guess_count += 1
        if self.guess_count == 1:
            self.feedback = feedback
            self.guesses = guess
        else:
            self.feedback = "%s, %s" % (self.feedback, feedback)
            self.guesses = "%s, %s" % (self.guesses, guess)
        if feedback == "GGGGG":
            self.status = False
            self.results = True
        elif self.guess_count == 6:
            self.status = False
            self.results = False
        db.session.add(self)
        db.session.commit()
                
    def create_payload(
        self, 
        include_correct=False, 
        include_feedback=False, 
        message=None
    ):
        payload = {
            'game_id': self.id,
            'token': self.token,
            'solver_id': self.solver_id,
            'solver_name': self.solver.name,
            'status': self.status,
            'guess_count': self.guess_count,
            'guesses': {},
            'correct_word': '*****',
            'message': 'None',
            'results': 'None'
        }
        if include_feedback == True:
            guess_list = self.guesses.split(', ')
            feedback_list = self.feedback.split(', ')
            feedback_dict = {}
            for i in range(len(guess_list)):
                feedback_dict[i + 1] = {"guess": guess_list[i], "feedback": feedback_list[i]}
            payload["guesses"] = feedback_dict
        if include_correct == True:
            payload["correct_word"] = self.correct_word
            if self.results == True:
                payload["results"] = 'won'
            else:
                payload["results"] = 'lost'
        if message != None:
            payload["message"] = message
        return payload

