from app import db
from datetime import datetime, timezone, timedelta
import secrets
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional


class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    solvers: so.WriteOnlyMapped['Solver'] = so.relationship(
                                            back_populates='user')
    games: so.WriteOnlyMapped['Game'] = so.relationship(
                                            back_populates='user')


class Solver(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    user_id: so.Mapped[int] = so.mapped_column(
                                            sa.ForeignKey(User.id), index=True)
    user: so.Mapped[User] = so.relationship(back_populates='solvers')
    words_played: so.Mapped[int] = so.mapped_column(default=0)
    words_won: so.Mapped[int] = so.mapped_column(default=0)
    games: so.WriteOnlyMapped['Game'] = so.relationship(back_populates='solver')

 
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

    