from app import db, login
from datetime import datetime, timezone, timedelta
from time import time
import secrets
import sqlalchemy as sa
from sqlalchemy import and_, func, desc
import sqlalchemy.orm as so
from typing import Optional, List
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app, url_for


class PaginatedAPIMixin(object):
    """
    Used for sending game lookup queries via an api request,
    This is a generic way that allows me do do this with other
    models as well if I have a need for it sometime in the future. 

    Code via The Flask Mega-Tutorial by Miguel Grinberg
    """
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = db.paginate(query, page=page, per_page=per_page,
                                error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            # Allows me to send games via api-links so I don't
            # send all of the data in one huge packet
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,    
                                **kwargs),
                'next': url_for(endpoint, page=page+1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page-1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                            unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    confirmed: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    solvers: so.Mapped[List['Solver']] = so.relationship(
            lazy="joined", cascade='all, delete-orphan', passive_deletes=True)
    games: so.Mapped[List['Game']] = so.relationship(
            lazy="joined", cascade='all, delete-orphan', passive_deletes=True)
    token: so.Mapped[Optional[str]] = so.mapped_column(
                                        sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]
   
    def to_dict(self):
        payload = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "solvers": [solver.name for solver in self.solvers]
        }
        return payload

    def get_api_token(self, expires_in=3600):
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(
                tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(
            seconds=1)

    @staticmethod
    def check_token(token):
        user = db.session.scalar(sa.select(User).where(User.token == token))
        if user is None or user.token_expiration.replace(
                tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return user

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


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
    api_id: so.Mapped[Optional[str]] = so.mapped_column(
                                    sa.String(32), index=True, unique=True, nullable=True, default=None)
    
    def to_dict(self):
        payload = {
            "api_id": self.api_id,
            "name": self.name,
            "words_played": self.words_played,
            "words_won": self.words_won,
            "avg_guesses": self.avg_guesses,
            "avg_won": self.avg,
            "max_streak": self.max_streak
        }
        return payload
    
    def make_api_id(self) -> str:
        self.api_id = secrets.token_hex(16)
        db.session.add(self)
        db.session.commit()
        return
    
    @staticmethod
    def check_api_id(key):
        solver = db.session.scalar(sa.select(Solver).where(Solver.api_id == key))
        return solver
    
    @staticmethod
    def get_solver(api_id: str):
        """Returns solver instance or None"""
        return db.session.scalar(sa.select(Solver).where(Solver.api_id == api_id))
    
    @staticmethod
    def validate_user_solver(username, solver_name) -> bool:
        user = db.session.scalar(
                        sa.select(User).where(User.username == username))
        solver = db.session.scalar(
                        sa.select(Solver).where(Solver.name == solver_name))
        if solver is None or user is None or user.id != solver.user_id:
            return False
        return True
        
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
           return sa.select(Game).order_by(desc(Game.id)).where(Game.solver_id == self.id)
        elif filter == "lost":
           return sa.select(Game).where(and_(Game.solver_id == self.id, Game.results == False)).order_by(desc(Game.id))
        elif filter == "won":
           return sa.select(Game).where(and_(Game.solver_id == self.id, Game.results == True)).order_by(desc(Game.id))


    def _update_stats(self):
        # Recalculates its stats based on all of the games played.
        games_played = db.session.scalar(
                        sa.select(
                        func.count(Game.id)).where(
                        Game.solver_id == self.id)
        )
        games_won = db.session.scalar(
                        sa.select(
                        func.count(Game.id)).where(
                        and_(Game.solver_id == self.id, Game.results == True))
        )
        self.words_played = games_played
        self.words_won = games_won
        self.calculate_avg_guesses
        db.session.add(self)
        db.session.commit()


class Game(PaginatedAPIMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    solver_id: so.Mapped[int] = so.mapped_column(
                                    sa.ForeignKey(Solver.id),index=True)
    user_id: so.Mapped[int] = so.mapped_column(
                                    sa.ForeignKey(User.id), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, 
                                    default=lambda: datetime.now(timezone.utc))
    solver: so.Mapped[Solver] = so.relationship(back_populates='games')
    correct_word: so.Mapped[str] = so.mapped_column(sa.String(10))
    guess_count: so.Mapped[int] = so.mapped_column(default=0)
    guesses: so.Mapped[Optional[str]] = so.mapped_column(sa.String(40), default='')
    feedback: so.Mapped[Optional[str]] = so.mapped_column(sa.String(40), default='')
    # True is won, False is Lost
    results: so.Mapped[Optional[bool]] = so.mapped_column(default=None)
                