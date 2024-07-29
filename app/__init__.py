from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mailman import Mail
from .games import GameCache

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to view this page!'
mail = Mail()
game_cache = GameCache()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configuring Flask Extensions 
    db.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    game_cache.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/')


    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app


from app import models