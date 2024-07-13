from app import create_app, db
from app.models import User, Solver, Game
from app import mail


app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Solver=Solver, Game=Game)
