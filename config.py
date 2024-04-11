import keyring
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = keyring.get_password("wordguess", "v8_dev")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'app.db')
    TESTING = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = 1
    MAIL_USERNAME = 'coalitionobscene@gmail.com'
    MAIL_PASSWORD = keyring.get_password("v8-email", "coalitionobscene")

    @staticmethod
    def init_app(app):
        pass


