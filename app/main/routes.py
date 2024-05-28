from flask import render_template, redirect, url_for, request, flash
from app.main import bp
from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db
from app.models import User, Solver, Game


@bp.route('/', methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.user', username=current_user.username))
    else:
        return render_template('index.html')
    
@bp.route('/documentation', methods=["GET"])
def documentation():
    return render_template("/documentation.html")


@login_required
@bp.route('/user/<username>', methods=["GET", 'POST'])
def user(username):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if not user:
        return redirect(url_for('index'))
    
    solvers = db.session.scalars(sa.select(Solver).where(Solver.user_id==user.id))
    return render_template('/user.html', user=user, solvers=list(solvers))

@login_required
@bp.route('/reset_solver', methods=["POST"])
def reset_solver():
    if request.method == "POST" and current_user.is_authenticated:
        solver_id = request.form.get("solver")
        solver = db.session.scalar(sa.select(Solver).where(
                                            Solver.id == solver_id))
        solver.reset_games()
        flash(f'{solver.name} has been reset!')
        return redirect(url_for('main.user', username=current_user.username))
    else:
        return redirect(url_for('main.index'))

@login_required
@bp.route('/delete_solver', methods=["POST"])
def delete_solver():
    if request.method == "POST" and current_user.is_authenticated:
        solver_id = request.form.get("solver")
        solver = db.session.scalar(sa.select(Solver).where(
                                            Solver.id == solver_id))
        name = solver.name
        db.session.execute(sa.delete(Solver).where(Solver.id == solver_id))
        db.session.commit()
        flash(f"{name} has been deleted!!")
        return redirect(url_for('main.user', username=current_user.username))
    else:
        return redirect(url_for('main.index'))
        

@login_required
@bp.route('/solver/<solver_name>', methods=["GET"])
def solver(solver_name):
    if current_user.is_authenticated:
        solver = db.session.scalar(sa.select(Solver).where(Solver.name == solver_name))
        # games = db.session.scalars(sa.select(Game).where(Game.solver_id == solver.id))

        game_query = sa.select(Game).where(
            Game.solver_id == solver.id).order_by(Game.id.desc())
        games = db.paginate(game_query, page=1, per_page=20, error_out=False).items
        return render_template('/solver.html', solver=solver, games=list(games))
    return redirect(url_for('main.index'))


@login_required
@bp.route('/create_api_key', methods=["POST"])
def create_new_key():
    if request.method == "POST" and current_user.is_authenticated:
        solver_id = request.form.get("solver")
        solver = db.session.scalar(sa.select(Solver).where(Solver.id == solver_id))
        new_api_key = solver.make_api_key()
        return redirect(url_for('main.solver', solver_name=solver.name))
    