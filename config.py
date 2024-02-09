import keyring


class Config:
    SECRET_KEY = keyring.get_password("wordguess", "v8_dev")

    @staticmethod
    def init_app(app):
        pass


