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


@bp.route('/user/<username>', methods=["GET"])
@login_required
def user(username):
    user = db.session.scalar(db.select(User).where(User.username == username))
    if not user.confirmed:
        flash('In order for you to use the WordGuessAPI you must confirm your account by clicking on the link sent via email. If you need another link, go to the account page and select "Resend Confirmation"')
    solvers = list(db.session.scalars(sa.select(Solver).where(Solver.user_id==user.id)))
    return render_template('/user.html', user=user, solvers=solvers)


@bp.route('/reset_solver', methods=["POST"])
@login_required
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


@bp.route('/delete_solver', methods=["POST"])
@login_required
def delete_solver():
    if request.method == "POST" and current_user.is_authenticated:
        solver_id = request.form.get("solver")
        solver = db.session.scalar(sa.select(Solver).where(
                                            Solver.id == solver_id))
        name = solver.name
        db.session.execute(sa.delete(Solver).where(Solver.id == solver_id))
        db.session.execute(sa.delete(Game).where(Game.solver_id == solver_id))
        db.session.commit()
        flash(f"{name} has been deleted!!")
        return redirect(url_for('main.user', username=current_user.username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/solver/<solver_name>/', methods=["GET"])
@login_required
def solver(solver_name, filter=None):
    if not current_user.is_authenticated:
        flash('Must be logged in to view solver pages')
        return redirect(url_for('main.index'))
    solver = db.session.scalar(sa.select(Solver)
                        .where(Solver.name == solver_name))
    if not solver or solver.user_id != current_user.id:
        flash(f"{solver.name} is not registered under your WordGuessAPI account.")
        return redirect(url_for('main.index'))
    page = request.args.get('games', 1, type=int)
    filter = request.args.get('filter')
    games = db.paginate(solver.get_games(filter=filter), page=page,
                            per_page=50, error_out=False)
    next_url = url_for('main.solver', solver_name=solver.name, 
                       filter=filter, games=games.next_num) \
            if games.has_next else None
    prev_url = url_for('main.solver', solver_name=solver.name, 
                       filter=filter, games=games.prev_num) \
            if games.has_prev else None
    return render_template('/solver.html', solver=solver, 
            prev_url=prev_url, next_url=next_url, games=games)
    
        
@bp.route('/create_api_id', methods=["POST"])
@login_required
def create_new_key():
    if request.method == "POST" and current_user.is_authenticated:
        solver_id = request.form.get("solver")
        solver = db.session.scalar(sa.select(Solver).where(Solver.id == solver_id))
        solver.make_api_id()
        return redirect(url_for('main.solver', solver_name=solver.name))
    