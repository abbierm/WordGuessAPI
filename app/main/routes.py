from flask import render_template, redirect, url_for, request, flash
from app.main import bp
from flask_login import current_user
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



@bp.route('/user/<username>', methods=["GET", 'POST'])
def user(username):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if not user:
        return redirect(url_for('index'))
    
    solvers = db.session.scalars(sa.select(Solver).where(Solver.user_id==user.id))
    return render_template('/user.html', user=user, solvers=list(solvers))


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
        
