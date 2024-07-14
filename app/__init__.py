from config import Config
from flask import Flask, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mailman import Mail

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to view this page!'
mail = Mail()

CONFIRMATION = 'Please check your email for a confirmation link!  Before using the WordGuessAPI your account/email must be confirmed!'


def create_app(config_class=Config):
    app = Flask(__name__)
    
    app.config.from_object(config_class)

    # Configuring Flask Extensions 
    db.init_app(app)
    login.init_app(app)
    mail.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/')


    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.before_request
    def remind_confirmation():
        print(session.get("_flashes", []))
        if current_user.is_authenticated and not \
                current_user.confirmed and not \
                ('message', CONFIRMATION) in session.get("_flashes", []):
            flash(CONFIRMATION)
            
    return app



from . import wordguess
from app import models