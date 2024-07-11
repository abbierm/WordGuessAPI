from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, RegisterSolver
import sqlalchemy as sa
from app import db
from app.models import User, Solver
from .email import send_password_reset_email, send_confirmation_email, send_update_new_email_confirmation


@bp.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit() or request.method == "POST":
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('auth/login.html', form=form)


@bp.route('/logout', methods=["GET"])
def logout():
    logout_user()
    flash("You have successfully been logged out!")
    return redirect(url_for("main.index")) 


@bp.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # Initial confirmation token 
        send_confirmation_email(user)
        flash('Congratulations, you are now a registered user!, Please check your email for a confirmation link that will allow you to use our API')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@bp.route('/confirm/<token>', methods=["GET"])
def verify_account(token):
    user = User.verify_account(token)
    if not user:
        flash('Invalid or expired confirmation link.')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('Your account has been verified.')
    return redirect(url_for('main.index'))


@bp.route('/resend_confirmation', methods=["GET"])
def resend_confirmation():
    if not current_user.is_authenticated:
        flash('You must have an account and be logged in to receive a new confirmation link.')
        return redirect(url_for('auth.login'))
    send_confirmation_email(current_user)
    flash('A new confirmation email has been sent!')
    return redirect(url_for('main.index'))


@bp.route('/reset_password_request', methods=["GET", "POST"])
def reset_password_request():
    if not current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user:
            user.confirmed=False
            db.session.add(user)
            db.session.commit()
            send_password_reset_email(user)
            flash('Check your email for a link to reset your password!')
            return redirect(url_for('auth.login'))
        else:
            flash('Unable to find account linked to that email.')
    return render_template('auth/reset_password_request.html', form=form)


@bp.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired reset token.')
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.confirmed=True
        db.session.commit()
        flash('Your password has been updated!')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/account', methods=["GET"])
@login_required
def account():
    if current_user.is_authenticated:
        return render_template('auth/account.html', user=current_user)
    else:
        return redirect(url_for('main.index'))


@bp.route('/register_solver', methods=["GET", "POST"])
@login_required
def register_solver():
    form = RegisterSolver()
    if form.validate_on_submit():
        user_id = current_user.id
        new_solver = Solver(name=form.name.data, user_id=user_id)
        db.session.add(new_solver)
        db.session.commit()
        flash(f'Congratulations! {new_solver.name} has now been created!  To start playing, go to the solver page from your homepage and click the link to create the new api key!!!')
        return redirect(url_for('main.user', username=current_user.username))
    return render_template('auth/register_solver.html', form=form)


@bp.route('/change_username', methods=["POST"])
@login_required
def change_username():
    if not current_user.is_authenticated or not request.method == "POST":
        return redirect(url_for('main.index'))
    new_name = request.form.get("new_username")
    if current_user.username == new_name:
        flash(f"{new_name} is already your username")
    elif User.check_duplicate_username(new_name):
        flash(f"{new_name} is already a registered to another account.")
    else:
        current_user.username = new_name
        db.session.add(current_user)
        db.session.commit()
        flash(f"Successfully changed username to {new_name}!")
    return redirect(url_for('auth.account', user=current_user))


@bp.route('/change_email', methods=["POST"])
@login_required
def change_email_request():
    if not current_user.is_authenticated or not request.method == "POST":
        return redirect(url_for('main.index'))
    new_email = request.form.get("new_email")
    if current_user.email == new_email:
        flash(f'{new_email} is already the email on file registered for this account')
    elif User.check_duplicate_email(new_email):
        flash(f"{new_email} is already registered to another account.")
    else:
        current_user.confirmed = False
        current_user.email = new_email
        db.session.add(current_user)
        db.session.commit()
        send_update_new_email_confirmation(current_user)
        flash(f"A confirmation has been sent to {new_email}!")
    return redirect(url_for('auth.account', user=current_user))


@bp.route('/change_email/<token>', methods=["GET"])
def change_email(token):
    user = user.verify_account(token)
    if not user:
        flash('Invalid or expired confirmation link.')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('Your new email has been confirmed!!!')
    return redirect(url_for('main.index'))
    
    

