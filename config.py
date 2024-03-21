import keyring
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = keyring.get_password("wordguess", "v8_dev")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'app.db')
    TESTING = False

    @staticmethod
    def init_app(app):
        pass


